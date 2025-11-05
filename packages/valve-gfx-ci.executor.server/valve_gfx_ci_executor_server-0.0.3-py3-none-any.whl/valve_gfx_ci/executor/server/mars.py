from threading import Thread, Event
from dataclasses import asdict, field, fields, KW_ONLY
from datetime import datetime, timedelta
from enum import StrEnum
from ipaddress import IPv4Address
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pprint import pprint

from deepdiff import DeepDiff
from pydantic.dataclasses import dataclass
from pydantic import field_validator, model_validator, PositiveInt
from inotify_simple import INotify, flags
import errno
import fcntl
import math

import threading
import traceback
import time
import yaml
import os

from .dhcpd import MacAddress
from .logger import logger
from .dut import DUT
from .job import NetworkEndpoint
from .job_source import JobSource
from .pdu import PDU
from .pdu.daemon import AsyncPDU
from . import config
from . import github
from . import gitlab


INVALID_TOKEN = "<invalid default>"


@dataclass
class ConfigEthernetDevice:
    _: KW_ONLY
    mac_address: str | None = None
    # NOTE: Make sure to expose the `ip_address` field when inheriting from this dataclass

    @field_validator('mac_address')
    @classmethod
    def mac_address_is_understood_by_boots(cls, v):
        if v:
            MacAddress(v)
        return v

    @property
    def hostname(self):
        return None


@dataclass
class ConfigPDU(ConfigEthernetDevice):
    driver: str
    config: dict
    reserved_port_ids: list[str] = field(default_factory=list)
    hidden: bool = False

    @property
    def ip_address(self) -> str:
        return self.config.get('hostname')

    @property
    def hostname(self):
        return getattr(self, "name", None)

    @model_validator(mode='after')
    def final_validation(self, v):
        if self.mac_address:
            # Ensure the hostname is an IPv4Address if a mac address is set, so
            # that it could be used for IP allocations
            IPv4Address(self.ip_address)
        return self

    def matches(self, other: 'ConfigPDU') -> bool:
        if other.mac_address and self.mac_address == other.mac_address:
            # The MAC address is unique, so there can't be two PDUs sharing it
            logger.info("mac address matches")
            return True

        if self.driver != other.driver:
            return False

        # Check if the other.config is a strict subset of self.config
        for cfg_name, cfg_value in other.config.items():
            if self.config.get(cfg_name, object()) != cfg_value:
                return False

        return True


@dataclass
class ConfigAclEntries:
    users: list[str] | None = field(default_factory=list)
    projects: list[str] | None = field(default_factory=list)
    projects_in_groups: list[str] | None = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any(getattr(self, attr.name) for attr in fields(self))

    def tags(self, *, prefix: str) -> set[str]:
        return {
            prefix + ':' + 'acl:' + attr.name + ':' + value
            for attr in fields(self)
            for value in getattr(self, attr.name)
        }


@dataclass
class ConfigAcl:
    """
    `deny` takes precedence over `allow`, and if neither matches, the next
    level up gets evaluated (dut/gateway acl > instance acl).
    If nothing matches, the default is `deny` if an acl was set anywhere in
    the chain, and `allow` if there is no acl.
    """
    deny: ConfigAclEntries | None = field(default_factory=ConfigAclEntries)
    allow: ConfigAclEntries | None = field(default_factory=ConfigAclEntries)

    def is_empty(self) -> bool:
        return all(getattr(self, attr.name).is_empty() for attr in fields(self))


@dataclass
class ConfigDUTJobSource:
    exposed: bool = True

    @property
    def db_job_source(self) -> 'ConfigJobSource':
        raise NotImplementedError

    @property
    def job_source(self) -> 'JobSource':
        return self.db_job_source.create_job_source(db_dut=self.dut, db_dut_job_src=self)

    @property
    def should_be_exposed(self) -> bool:
        if parent_priority_queues := getattr(self, "parent_priority_queues", None):
            if not parent_priority_queues.exposed:
                return False

        return self.db_job_source.expose_runners and self.exposed

    @property
    def description(self):
        if dut := self.dut:
            return dut.full_name
        else:
            return f"{config.FARM_NAME}-gateway"

    @property
    def tags(self):
        if dut := self.dut:
            tags = dut.all_tags
        else:
            tags = gitlab.generate_gateway_runner_tags(self.db_job_source.gateway_runner)

        if priority := getattr(self, "priority", None):
            tags += [f"ci-tron:priority:{priority}"]

        return tags

    @property
    def details(self) -> dict[str, str]:
        """Return details about how the dut is exposed on the job source"""
        return {}

    @property
    def has_valid_token(self) -> bool:
        return True

    @property
    def is_valid(self):
        return True

    def verify_or_renew(self) -> None:
        pass

    def remove(self) -> bool:
        return True


@dataclass
class ConfigGitlabRunner(ConfigDUTJobSource):
    token: str = INVALID_TOKEN
    runner_id: int = -1
    acl: ConfigAcl | None = None

    @property
    def db_job_source(self) -> 'ConfigGitlab':
        if instance := self.mars_db.gitlab.get(self.name):
            return instance
        else:
            raise ValueError(f"GitLab instance {self.name} does not exist")

    @property
    def details(self) -> dict[str, str]:
        gl = self.db_job_source

        data = {
            "instance": str(gl.url.removeprefix("https://").removesuffix("/")),
            "maximum_timeout": f"{gl.maximum_timeout} seconds",
            "runner_type": str(gl.runner_type),
            "runner_id": str(self.runner_id),
        }

        if gl.runner_type == gitlab.RunnerType.GROUP:
            data["group_id"] = str(gl.group_id)
        elif gl.runner_type == gitlab.RunnerType.PROJECT:
            data["project_id"] = str(gl.project_id)

        return data

    @property
    def _log_prefix(self):
        priority_str = ""
        if priority := getattr(self, "priority", None):
            priority_str = f" {priority} priority" if priority else ""

        return f"{self.description}'s{priority_str} {self.db_job_source.name} runner (#{self.runner_id})"

    @property
    def has_valid_token(self):
        return self.token != INVALID_TOKEN

    @property
    def is_valid(self):
        return self.has_valid_token and self.runner_id >= 0

    def verify_or_renew(self) -> None:
        def remove_and_register():
            logger.warning(f"{log_prefix}: Starting the renewal process...")

            if not self.remove():
                logger.error(f"{log_prefix}: Could not unregister the runner on {gl.name}")
                return

            if gl.has_valid_looking_registration_token:
                runner = gitlab.register_runner(gitlab_url=gl.url,
                                                registration_token=gl.registration_token,
                                                description=self.description,
                                                tag_list=self.tags,
                                                maximum_timeout=gl.maximum_timeout,
                                                runner_type=gl.runner_type,
                                                group_id=gl.group_id,
                                                project_id=gl.project_id)
                if runner:
                    self.token = runner.token
                    self.runner_id = runner.id
                    logger.info(f"{log_prefix}: Got assigned a token")
                else:
                    logger.error(f"{log_prefix}: Could not register the runner on {gl.name}")
            else:
                logger.error(f"{log_prefix}: No registration tokens specified. Aborting...")

        try:
            # Figure out the list of tags and description for the runner by either sourcing it from the associated DUT,
            # or considering it as a gateway runner
            gl = self.db_job_source
            log_prefix = self._log_prefix

            # Exit early if we are not supposed to expose the DUT
            if not self.should_be_exposed:
                self.remove()
                return

            logger.debug(f"{log_prefix}: Verifying the token")
            if not gitlab.verify_runner_token(gitlab_url=gl.url,
                                              token=self.token) or self.runner_id < 0:
                logger.warning(f"{log_prefix}: The token {self.token} is invalid.")
                remove_and_register()
            else:
                # The runner token is valid, let's check that the tags and description match!
                if gl.has_valid_looking_access_token:
                    runner = gitlab.runner_details(gitlab_url=gl.url, private_token=gl.access_token,
                                                   runner_id=self.runner_id)

                    if runner is not None:
                        needs_re_registering = False
                        if runner.description != self.description:
                            logger.warning(f"{log_prefix}: The runner's description does not match the local value")
                            needs_re_registering = True
                        elif set(runner.tag_list) != set(self.tags):
                            logger.warning(f"{log_prefix}: The runner tags list does not match the local database")
                            needs_re_registering = True
                        elif runner.maximum_timeout != gl.maximum_timeout:
                            logger.warning(f"{log_prefix}: The runner's maximum timeout does not match the local value")
                            needs_re_registering = True

                        if needs_re_registering:
                            remove_and_register()
                else:
                    logger.warning(f"{log_prefix}: No access token specified, skipping tags verification")
        except Exception:
            logger.error(traceback.format_exc())

    def remove(self) -> bool:
        if not super().remove():
            return False

        if not self.has_valid_token:
            return True

        logger.info(f"{self._log_prefix}: Unregister the runner token")
        if not gitlab.unregister_runner(gitlab_url=self.db_job_source.url, token=self.token):
            # We failed to remove the runner, make sure the token is still valid
            if gitlab.verify_runner_token(gitlab_url=self.db_job_source.url, token=self.token):
                return False

        self.token = INVALID_TOKEN
        self.runner_id = -1

        return True


@dataclass
class ConfigGithubRunner(ConfigDUTJobSource):
    runner_group_id: int | None = None

    @property
    def db_job_source(self) -> 'ConfigGithub':
        if instance := self.mars_db.github.get(self.name):
            return instance
        else:
            raise ValueError(f"GitHub instance {self.name} does not exist")

    @property
    def details(self) -> dict[str, str]:
        gh = self.db_job_source

        return {
            "namespace": gh.namespace,
            "runner_group_id": str(gh.runner_group_id),
        }

    def remove(self) -> bool:
        self.exposed = False
        return True


@dataclass
class ConfigDUTJobSourcePriorityQueues:
    exposed: bool = True

    # key is the priority name
    priority_queues: dict[str, ConfigGitlabRunner | ConfigGithubRunner] = field(default_factory=dict)


@dataclass
class ConfigDUTGitlabPriorityQueues(ConfigDUTJobSourcePriorityQueues):
    acl: ConfigAcl | None = None


@dataclass
class ConfigDUTGithubPriorityQueues(ConfigDUTJobSourcePriorityQueues):
    pass


@dataclass
class ConfigDUT(ConfigEthernetDevice):
    base_name: str
    ip_address: str  # TODO: Make sure all machines have a unique IP
    tags: list[str]
    manual_tags: list[str] = field(default_factory=list)
    local_tty_device: str | None = None
    # key is the gitlab instance name
    gitlab: dict[str, ConfigDUTGitlabPriorityQueues | ConfigGitlabRunner] = field(default_factory=dict)
    github: dict[str, ConfigDUTGithubPriorityQueues | ConfigGithubRunner] = field(default_factory=dict)
    pdu: str | None = None
    pdu_port_id: str | int | None = None
    pdu_off_delay: float = 30
    firmware_boot_time: float | None = None  # Maximum amount of time the firmware can take before advertising itself
    boot_sequence_power: float | None = None  # Average amount of power (W) consumed by the DUT during its boot sequence
    ready_for_service: bool = False
    is_retired: bool = False
    first_seen: datetime = field(default_factory=lambda: datetime.now())
    comment: str | None = None

    @property
    def db_dut_job_sources_fields(self) -> dict[str, tuple[ConfigDUTJobSourcePriorityQueues, ConfigDUTJobSource]]:
        return {
            "gitlab": (ConfigDUTGitlabPriorityQueues, ConfigGitlabRunner),
            "github": (ConfigDUTGithubPriorityQueues, ConfigGithubRunner),
        }

    def __post_init__(self):
        for dut_job_src in self.db_dut_job_sources_fields:
            for instance_name, runner_or_queues in getattr(self, dut_job_src, {}).items():
                runner_or_queues.name = instance_name
                runner_or_queues.dut = self

    @field_validator('pdu_port_id')
    @classmethod
    def convert_pdu_port_id_to_str(cls, v):
        return str(v)

    @field_validator('ip_address')
    @classmethod
    def ip_address_is_valid(cls, v):
        IPv4Address(v)
        return str(v)

    @field_validator('firmware_boot_time')
    @classmethod
    def firmware_boot_time_is_valid(cls, v):
        # No time has been learnt yet, and it is ok
        if v is None:
            return v

        if not isinstance(v, int) and not isinstance(v, float):
            raise ValueError("Invalid type")

        if v <= 0:
            raise ValueError("The firmware boot time must be a positive number")

        return float(v)

    @field_validator('boot_sequence_power')
    @classmethod
    def boot_sequence_power_is_valid(cls, v):
        # No power usage has been learnt yet, and it is ok
        if v is None:
            return v

        if not isinstance(v, int) and not isinstance(v, float):
            raise ValueError("Invalid type")

        if v <= 0:
            raise ValueError("The boot_sequence_power must be a positive number")

        return round(float(v), 1)

    @model_validator(mode='after')
    def final_validation(self, v):
        for field_name in ["ip_address", "mac_address"]:
            if not getattr(self, field_name, None):
                raise ValueError(f"The field `{field_name}` cannot be empty")
        return self

    @property
    def full_name(self):
        # Get the index of the dut by looking at how many duts with
        # the same base name were registered *before* us.
        idx = 1
        for dut in self.mars_db.duts.values():
            if dut.base_name == self.base_name and dut.first_seen < self.first_seen:
                idx += 1

        return f"{config.FARM_NAME}-{self.base_name}-{idx}"

    @property
    def hostname(self):
        hostname = f"dut-{self.full_name}"
        if len(hostname) < 32:
            return hostname
        else:
            return hostname[0:15] + '...' + hostname[-13:]

    # List of attributes that are safe to expose publicly
    @property
    def safe_attributes(self):
        return {
            "id": self.id,
            "base_name": self.base_name,
            "full_name": self.full_name,
            "hostname": self.hostname,
            "tags": self.tags,
            "manual_tags": self.manual_tags,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "local_tty_device": self.local_tty_device,
            "firmware_boot_time": self.firmware_boot_time,
            "boot_sequence_power": self.boot_sequence_power,
            "ready_for_service": self.ready_for_service,
            "comment": self.comment
        }

    @property
    def all_tags(self):
        farm_tags = [f"farm:{config.FARM_NAME}"]
        return sorted(set(self.tags + self.manual_tags + farm_tags))

    @property
    def available(self):
        return self.ready_for_service and not self.is_retired

    @property
    def db_dut_job_sources(self) -> list['ConfigDUTJobSource']:
        db_dut_job_sources = list()

        # Provide the name of the instance to the ConfigDUTJobSource
        stale_db_dut_job_sources = []
        for dut_job_src_name in self.db_dut_job_sources_fields:
            dut_job_src = getattr(self, dut_job_src_name, {})
            for instance_name, runner_or_priority_queues in dut_job_src.items():
                if isinstance(runner_or_priority_queues, ConfigDUTJobSource):
                    queues = {"default": runner_or_priority_queues}
                    parent_priority_queues = None
                else:
                    queues = runner_or_priority_queues.priority_queues
                    parent_priority_queues = runner_or_priority_queues

                for priority, runner in queues.items():
                    runner.dut = self
                    runner.mars_db = self.mars_db
                    runner.name = instance_name
                    runner.priority = priority
                    runner.parent_priority_queues = parent_priority_queues

                    # Remove the DB DUT job source if its priority is not listed in the instance's priorities
                    if priority not in runner.db_job_source.priorities:
                        stale_db_dut_job_sources.append(runner)
                    else:
                        db_dut_job_sources.append(runner)

        # Remove all the stale db DUT job sources from the
        for db_dut_job_src in stale_db_dut_job_sources:
            logger.warning((f"{self.full_name}: Removing the runner {db_dut_job_src.name}/{db_dut_job_src.priority} "
                            "because the priority does not exist"))

            # Remove the runner from the job source
            db_dut_job_src.remove()

            # Remove the stale entry in MarsDB
            if parent := db_dut_job_src.parent_priority_queues:
                del parent.priority_queues[db_dut_job_src.priority]

        return db_dut_job_sources

    def expose_on_job_sources(self):
        try:
            # Make sure every job source instance is represented in the DUT's config
            for job_src_field_name, job_src_field_types in self.db_dut_job_sources_fields.items():
                db_dut_job_sources = getattr(self, job_src_field_name)

                # Add all the job source instances defined in marsDB that are currently missing in the DUT
                for db_job_src in getattr(self.mars_db, job_src_field_name, {}).values():
                    if db_job_src.name not in db_dut_job_sources:
                        exposed = db_job_src.expose_all_runners_by_default
                        db_dut_job_sources[db_job_src.name] = job_src_field_types[0](exposed=exposed)

                    # Make sure every priority of the job source is represented in the DUT job source
                    db_dut_job_source = db_dut_job_sources[db_job_src.name]
                    for priority in db_job_src.priorities:
                        if priority not in db_dut_job_source.priority_queues:
                            db_dut_job_source.priority_queues[priority] = job_src_field_types[1](exposed=True)

            for db_dut_job_src in self.db_dut_job_sources:
                db_dut_job_src.verify_or_renew()
        except Exception:
            logger.error(traceback.format_exc())

    def remove_from_job_sources(self):
        # Un-register every associated runner
        for db_dut_job_src in self.db_dut_job_sources:
            db_dut_job_src.remove()


@dataclass
class ConfigPrioritySettings:
    pass


@dataclass
class ConfigGitlabPrioritySettings:
    acl: ConfigAcl | None = None


@dataclass(kw_only=True)
class ConfigJobSource:
    expose_runners: bool
    expose_all_runners_by_default: bool = True

    # None means jobs.priorities applies
    exposed_priorities: dict[str, ConfigPrioritySettings] | None = None

    @property
    def priorities(self) -> list[str]:
        """Return the list of priorities this job source exposes runners at, ordered in priority order"""
        global_priorities = self.mars_db.jobs.priorities

        if self.exposed_priorities is None:
            # None means jobs.priorities applies
            return global_priorities
        else:
            return sorted(self.exposed_priorities.keys(), key=global_priorities.index)

    def create_job_source(self, db_dut: ConfigDUT, db_dut_job_src: ConfigDUTJobSource) -> JobSource:
        raise NotImplementedError


@dataclass(kw_only=True)
class ConfigGitlab(ConfigJobSource):
    # override the default ConfigJobSource fields
    exposed_priorities: dict[str, ConfigGitlabPrioritySettings] | None = None

    url: str
    registration_token: str | None = None
    runner_type: gitlab.RunnerType | None = gitlab.RunnerType.INSTANCE
    group_id: PositiveInt | None = None
    project_id: PositiveInt | None = None
    access_token: str | None = None
    maximum_timeout: PositiveInt = 21600
    gateway_runner: ConfigGitlabRunner | None = None
    acl: ConfigAcl | None = None

    @field_validator("url")
    @classmethod
    def url_is_valid(cls, v):
        if v.startswith("https://"):
            return v
        elif v.startswith("http://") and config.as_boolean('GITLAB_ALLOW_INSECURE'):
            return v

        raise ValueError("The GitLab URL should start with 'https://', or with "
                         "'http://' if the environment variable "
                         "'GITLAB_ALLOW_INSECURE' is set to 'true'")

    def has_valid_looking_token(self, token):
        return isinstance(token, str) and len(token) >= 8

    @property
    def has_valid_looking_registration_token(self):
        return self.has_valid_looking_token(self.registration_token)

    @property
    def has_valid_looking_access_token(self):
        return self.has_valid_looking_token(self.access_token)

    @property
    def should_expose_gateway_runner(self):
        if not self.expose_runners or self.gateway_runner is None:
            return False

        if self.gateway_runner.acl is None or self.gateway_runner.acl.allow.is_empty():
            return False

        return self.gateway_runner.exposed

    def create_job_source(self, db_dut: ConfigDUT, db_dut_job_src: ConfigGitlabRunner) -> JobSource:
        return gitlab.GitlabJobSource(job_src=self, db_dut=db_dut, db_dut_job_src=db_dut_job_src)


@dataclass(kw_only=True)
class ConfigGithub(ConfigJobSource):
    URL_PREFIX = "https://api.github.com/"

    url: str | None = None
    authorization_token: str | None = None
    runner_group_id: int | None = None

    @field_validator("url")
    @classmethod
    def url_is_valid(cls, v):
        if v.startswith(cls.URL_PREFIX):
            return v

        raise ValueError("The GitHub URL should start with 'https://api.github.com/'")

    @field_validator("runner_group_id")
    @classmethod
    def runner_group_id_is_valid(cls, v):
        if v is None:
            return v
        if v > 0:
            return v

        raise ValueError("The runner_group_id should be number > 0'")

    @property
    def namespace(self) -> str:
        return self.url.removeprefix(self.URL_PREFIX)

    def create_job_source(self, db_dut: ConfigDUT, db_dut_job_src: ConfigGithubRunner) -> JobSource:
        return github.GithubJobSource(job_src=self, db_dut=db_dut, db_dut_job_src=db_dut_job_src)


@dataclass
class ConfigJobProxy:
    allowed_endpoints: list[NetworkEndpoint] = field(default_factory=list)


@dataclass
class ConfigJob:
    proxy: ConfigJobProxy = field(default_factory=ConfigJobProxy)
    priorities: list[str] = field(default_factory=lambda: ['default'])


@dataclass
class MarsDB:
    pdus: dict[str, ConfigPDU] = field(default_factory=dict)
    duts: dict[str, ConfigDUT] = field(default_factory=dict)
    gitlab: dict[str, ConfigGitlab] = field(default_factory=dict)
    github: dict[str, ConfigGithub] = field(default_factory=dict)
    jobs: ConfigJob = field(default_factory=ConfigJob)

    def reset_taint(self):
        self._disk_state = asdict(self)

    @property
    def diff_from_disk_state(self):
        return DeepDiff(self._disk_state, asdict(self), ignore_order=True)

    @property
    def is_tainted(self):
        return len(self.diff_from_disk_state) > 0

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent
    def __post_init__(self):
        # When no PDUs are set in mars db, automatically add or update the VPDU
        # if the parameter is set. This protects against other things that might
        # externally modify (or generate) the mars db (e.g. vivian from the
        # CI-tron project.)
        if config.EXECUTOR_VPDU_ENDPOINT:
            vpdu_config = {"hostname": config.EXECUTOR_VPDU_ENDPOINT}
            if "VPDU" in self.pdus:
                self.pdus["VPDU"].driver = "vpdu"
                self.pdus["VPDU"].config = vpdu_config
            elif len(self.pdus) == 0:
                self.pdus["VPDU"] = ConfigPDU(driver="vpdu", config=vpdu_config)

        # Since we do not want to repeat ourselves in the config file, the name
        # of objects is set in the parent dict. However, it is quite useful for
        # objects to know their names and have access to the DB. This function
        # adds it back!
        for name, pdu in self.pdus.items():
            pdu.name = name
            pdu.mars_db = self

        for dut_id, dut in self.duts.items():
            dut.id = dut_id
            dut.mars_db = self

        for job_source_type in [self.gitlab, self.github]:
            for name, instance in job_source_type.items():
                instance.name = name
                instance.mars_db = self

                if gateway_runner := getattr(instance, 'gateway_runner', None):
                    gateway_runner.mars_db = self
                    gateway_runner.name = instance.name
                    gateway_runner.dut = None

        self.reset_taint()

        # Ensure the default priority is found in the global list of priorities
        if "default" not in self.jobs.priorities:
            self.jobs.priorities.append("default")

        # Ensure all the dut job sources have an associated instance, and all the invalid runners get removed
        for dut_id, dut in self.duts.items():
            for db_dut_job_src in dut.db_dut_job_sources:
                db_dut_job_src.db_job_source

        # Perform migrations after resetting the taint so that if the content
        # is modified by any migration, we will end up writing it back to disk

        # 2024/03/21 Migration: If the MAC Address is not set but the dut ID
        # looks like one, make it the mac address too.
        for dut_id, dut in self.duts.items():
            if dut.mac_address is None:
                try:
                    MacAddress(dut_id)
                    dut.mac_address = dut_id
                except Exception:
                    pass

        # 2025/10/02 Migration: Ensure MAC addresses are unique throughout the DB,
        # after we introduced alternate MAC addresses
        mac_addresses_seen = set()
        for dut in self.duts.values():
            i = 0
            while dut.mac_address in mac_addresses_seen:
                i = i + 1
                dut.mac_address = MacAddress.from_serial(f"{dut.id}-{i}")
            mac_addresses_seen.add(dut.mac_address)

        # 2025/10/17 Migration: Remove empty ACLs
        # The first version of the ACL code created an empty one every time,
        # but this turned out to be too spammy, so cleanup the ones that never
        # got filled.
        for dut in self.duts.values():
            for gl_runner in dut.gitlab.values():
                if gl_runner.acl is not None and gl_runner.acl.is_empty():
                    gl_runner.acl = None

        for gl_instance in self.gitlab.values():
            if gl_instance.acl is not None and gl_instance.acl.is_empty():
                gl_instance.acl = None
            if gateway_runner := gl_instance.gateway_runner:
                if gateway_runner.acl is not None and gateway_runner.acl.is_empty():
                    gateway_runner.acl = None

        # 2025-10-17 Migration: transition the DUTs into the priority queues era.
        # Existing farm owners are exposing it to Mesa CI, which expect high & low priorities on top of the default one.
        migrating_priority_queues = True
        for dut in self.duts.values():
            for gl_runner in dut.gitlab.values():
                if isinstance(gl_runner, ConfigDUTGitlabPriorityQueues):
                    # Consider any ConfigDUTGitlabPriorityQueues set in MarsDB as having been written post-migration
                    migrating_priority_queues = False

        if migrating_priority_queues:
            logger.warning("# Perform the priority queue migration #")

            # Set the default ['high', 'default', 'low']
            gl_exposed_priorities = {
                "high": ConfigGitlabPrioritySettings(),
                "default": ConfigGitlabPrioritySettings(),
                "low": ConfigGitlabPrioritySettings(),
            }

            # Set gitlab/github instances' default list of priorities to ["default"], except for gl.fd.o which
            # requires ["high", "default", "low"]
            for gl_instance in self.gitlab.values():
                if gl_instance.url.startswith("https://gitlab.freedesktop.org"):
                    gl_instance.exposed_priorities = gl_exposed_priorities.copy()

                    # Only override the global priorities if we have found at least one gl.fd.o instance
                    self.jobs.priorities = list(gl_exposed_priorities.keys())
                elif gl_instance.exposed_priorities is None:
                    gl_instance.exposed_priorities = {
                        "default": ConfigGitlabPrioritySettings(),
                    }

            for gh_instance in self.github.values():
                if gh_instance.exposed_priorities is None:
                    gh_instance.exposed_priorities = {
                        "default": ConfigPrioritySettings(),
                    }

            for dut in self.duts.values():
                for instance_name, runner_or_priority_queues in dut.gitlab.copy().items():
                    if isinstance(runner_or_priority_queues, ConfigDUTJobSource):
                        # Remove the runner from the gitlab instance so that we don't leak it
                        runner_or_priority_queues.remove()

                        # Replace the ConfigGitlabRunner with a ConfigDUTGitlabPriorityQueues
                        # NOTE: Its list of priority queues will get populated by DUT.expose_on_job_sources()
                        prio_queues = ConfigDUTGitlabPriorityQueues(exposed=runner_or_priority_queues.exposed)
                        dut.gitlab[instance_name] = prio_queues

                # Ensure all the dut job sources have had their extra fields set (mars_db, dut, priority, ...)
                dut.db_dut_job_sources

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as f:
            cls.__dbLock(f)
            data = yaml.safe_load(f)
            return cls(**data if data else {})

    def save(self, file_path):
        with open(file_path, 'w') as f:
            self.__dbLock(f)
            # Needed until https://github.com/yaml/pyyaml/pull/901 is merged
            yaml.add_multi_representer(StrEnum, yaml.representer.SafeRepresenter.represent_str)
            yaml.dump(asdict(self), f, sort_keys=False)
            f.flush()
            os.fsync(f.fileno())
        self.reset_taint()

    # __dbLock returns as soon as an exclusive lock is acquired, else will
    # retry 5 times over 5 seconds, and raise a RuntimeError if unable to
    # acquire the lock after that period.
    @staticmethod
    def __dbLock(file):
        for _ in range(5):
            try:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                if e.errno in [errno.EACCES, errno.EAGAIN]:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"unable to lock file: {file.filename}")

            # lock successfully acquired
            return

        raise RuntimeError(f"timed out trying to lock file: {file.filename}")


class MarsDBAccess:
    def __init__(self, mars, readonly: bool = False):
        self._mars = mars
        self.entered_at = None
        self.readonly = readonly

    def __enter__(self):
        start = time.monotonic()
        self._mars._db_lock.acquire()
        self.entered_at = time.monotonic()

        # Upgrade the lock to be read-write if necessary, but never make it readonly
        if not self.readonly:
            self._mars._db_lock_readonly = False

        acquisitation_time_ms = (self.entered_at - start) * 1000.0
        if acquisitation_time_ms > 100:
            logger.warning(f"MaRS DB lock took an unusually long time to acquire: {acquisitation_time_ms:.1f} ms")

        return self._mars._db

    def __exit__(self, *args):
        # Only check if the database needs saving if release() would release the lock.
        # In other words, we only want to check if the database changed in the outermost level.
        if self._mars._db_lock._recursion_count() == 1:
            self._mars.save_db_if_needed()
            self._mars._db_lock_readonly = True
        self._mars._db_lock.release()

        held_time = (time.monotonic() - self.entered_at) * 1000.0
        if held_time > 100:
            logger.warning((f"MaRS DB lock held for an unusually long time: {held_time:.1f} ms."
                            f"Backtrace: {traceback.format_stack()}"))


class Mars(Thread):
    def __init__(self, pdu_daemon):
        super().__init__(name='MarsClient')

        self.pdu_daemon = pdu_daemon

        self._db = None
        self._db_lock = threading.RLock()  # Reentrant lock
        self._db_lock_readonly = True

        self._duts = {}
        self._discover_data = None

        self.stop_event = Event()

    @property
    def discover_data(self):
        if self._discover_data:
            delta = time.monotonic() - self._discover_data.get('started_at')
            if delta >= self._discover_data.get('timeout'):
                self._discover_data = None

        return self._discover_data

    @discover_data.setter
    def discover_data(self, value):
        if isinstance(value, dict) and not value:
            value = None

        self._discover_data = value

    def machine_discovered(self, dut_data, update_if_already_exists=False):
        machine = self.get_machine_by_id(dut_data.get('id'), raise_if_missing=False)

        if machine is None and self.discover_data:
            with self.db:
                # A new machine is about to be added through the discovery process

                pdu_port_id = self.discover_data.get('port_id')
                pdu_name = self.discover_data.get('pdu')

                machine = None
                if pdu_port := self.get_pdu_port_by_name(pdu_name, pdu_port_id):
                    dut_data["pdu_port_id"] = pdu_port_id
                    dut_data["pdu"] = pdu_name
                    dut_data["pdu_off_delay"] = pdu_port.pdu.default_min_off_time
                else:
                    logger.error(f"Discovery failed: The PDU port {pdu_name}/{pdu_port_id} doesn't exist in our DB")
                    # NOTE: We still want to create the DUT

                dut_data["firmware_boot_time"] = math.ceil(time.monotonic() - self.discover_data.get('started_at'))

                # We used the discovery data, so let's remove all of it
                self.discover_data = {}

                return self.add_or_update_machine(dut_data)
        elif machine is None:
            logger.warning("New machine found, despite no discovery process being in progress")

        if update_if_already_exists:
            return self.add_or_update_machine(dut_data)

    def pdu_discovered(self, pdu: PDU, mac_address: str = None):
        new_pdu = ConfigPDU(mac_address=mac_address, driver=pdu.driver_name, config=pdu.config)
        new_pdu.name = pdu.name

        logger.debug(f"PDU discovered: {new_pdu}")

        with self.db as mars_db:
            # Try to match the discovered PDU to a PDU we have in our configuration
            for pdu_name, pdu in mars_db.pdus.items():
                if pdu.matches(new_pdu):
                    logger.debug(f"  --> Ignored due to matching an already-configured PDU ({pdu})")
                    # We found a matching PDU, keep the existing one which supposedly works
                    return

            # No PDU matched, so let's add the new PDU
            logger.info(f"New PDU discovered and added to MarsDB: {new_pdu}")
            mars_db.pdus[new_pdu.name] = new_pdu

            # Update the associated PDU in the PDU Daemon
            self.get_pdu_by_name(new_pdu.name)

    @property
    def db(self):
        return MarsDBAccess(self, readonly=False)

    @property
    def db_readonly(self):
        return MarsDBAccess(self, readonly=True)

    @property
    def known_machines(self):
        with self.db_readonly:
            return list(self._duts.values())

    @property
    def known_ethernet_devices(self) -> list[ConfigEthernetDevice]:
        with self.db_readonly:
            return list(self._db.pdus.values()) + list(self._db.duts.values())

    def get_machine_by_id(self, machine_id, raise_if_missing=False):
        with self.db_readonly:
            machine = self._duts.get(machine_id)
            if machine is None:
                # We could not find the machine by its actual ID, try finding it by full_name instead!
                for dut in self._duts.values():
                    if dut.full_name == machine_id:
                        machine = dut
                        break

            if machine is None and raise_if_missing:
                raise ValueError(f"Unknown machine ID '{machine_id}'")
            return machine

    def get_machine_by_ip_address(self, ipaddr, raise_if_missing=False) -> DUT:
        with self.db_readonly:
            for dut in self._duts.values():
                if dut.ip_address == ipaddr:
                    return dut

            if raise_if_missing:
                raise ValueError(f"No DUT has '{ipaddr}' as an IP address")

    def _machine_update_or_create(self, db_dut):
        with self.db:
            dut = self._duts.get(db_dut.id)
            if dut is None:
                dut = DUT(mars=self, db_dut=db_dut)
                self._duts[dut.id] = dut
            else:
                dut.config_changed(db_dut=db_dut)

            self._db.duts[dut.id] = db_dut

            return dut

    def get_pdu_by_name(self, pdu_name, raise_if_missing=False):
        with self.db_readonly as mars_db:
            if pdu_cfg := mars_db.pdus.get(pdu_name):
                return self.pdu_daemon.get_or_create(pdu_cfg.driver, pdu_cfg.name,
                                                     pdu_cfg.config, pdu_cfg.reserved_port_ids,
                                                     hidden=pdu_cfg.hidden,
                                                     update_if_existing=True)

        if raise_if_missing:
            raise ValueError(f'PDU "{pdu_name}" does not exist')

    def get_pdu_port_by_name(self, pdu_name, pdu_port_id, raise_if_missing=False, timeout=None):
        with self.db_readonly:
            pdu = self.get_pdu_by_name(pdu_name, raise_if_missing)

            if port := pdu.get_port_by_id(pdu_port_id, timeout=timeout):
                return port

        if raise_if_missing:
            raise ValueError(f'PDU "{pdu_name}" does not have a port ID named {pdu_port_id}')

    @property
    def known_pdus(self) -> dict[str, AsyncPDU]:
        with self.db_readonly as mars_db:
            return {p: self.get_pdu_by_name(p) for p in mars_db.pdus}

    def save_db_if_needed(self):
        assert self._db_lock._is_owned()
        assert self._db_lock._recursion_count() > 0

        if not self._db_lock_readonly and self._db.is_tainted:
            print("Write-back the MarsDB to disk, after some local changes:")
            pprint(self._db.diff_from_disk_state, indent=2)
            print()

            self._db.save(config.MARS_DB_FILE)

    def add_or_update_machine(self, fields: dict):
        with self.db:
            dut_id = fields.pop("id")

            if db_dut := self._db.duts.get(dut_id):
                cur_state = asdict(db_dut)
                db_dut = ConfigDUT(**(cur_state | fields))
            else:
                db_dut = ConfigDUT(**fields)

            # TODO: Try to find a way not to have to add these fields
            db_dut.id = dut_id
            db_dut.mars_db = self._db
            db_dut.db_dut_job_sources

            machine = self._machine_update_or_create(db_dut)

        return machine

    def remove_machine(self, machine_id):
        with self.db:
            machine = self._duts.pop(machine_id, None)
            if not machine:
                return False

            # Remove the associated DUT in MaRS DB
            self._db.duts.pop(machine_id, None)

        # Stop thread
        machine.stop_machine(cancel_job=True, wait=True)

        # Kill the gitlab runner token
        machine.remove_from_job_sources()

        return True

    def sync_machines(self):
        with self.db:
            self._db = MarsDB.from_file(config.MARS_DB_FILE)

            local_only_machines = set(self.known_machines)
            for m in self._db.duts.values():
                machine = self._machine_update_or_create(m)

                # Remove the machine from the list of local-only machines
                local_only_machines.discard(machine)

            # Delete all the machines that are not found in MaRS
            for machine in local_only_machines:
                self._duts[machine.id].stop_machine(cancel_job=True, wait=False)
                del self._duts[machine.id]

            logger.info("Generate the GitLab runner access control script, and exposing the runners.")

            # Load gitlab-runner `pre_build_script` template
            acl_script_template = gitlab.load_access_control_template()

            for gl_name, gl in self._db.gitlab.items():
                # Convert the gateway runner's ACL to a gitlab-runner `pre_build_script`
                if gl.gateway_runner:
                    gitlab.write_access_control_script(template=acl_script_template, gl_name=gl_name,
                                                       dut_id=None, acls=[gl.gateway_runner.acl, gl.acl])

            # NOTE: We should release the lock before doing any sort of IO, but doing so will require a big refactor
            # of the module... so we instead run ten requests in parallel to speed the process up.
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Expose the gateway runners
                for gl in self._db.gitlab.values():
                    if gl.should_expose_gateway_runner:
                        executor.submit(gl.gateway_runner.verify_or_renew)

                # Configure the DUTs
                for m in self._db.duts.values():
                    executor.submit(m.expose_on_job_sources)

        # Update the gateway runner configuration
        gitlab.generate_gateway_runner_config(self._db)

    def stop(self, wait=True):
        self.stop_event.set()

        # Signal all the executors we want to stop
        for machine in self.known_machines:
            machine.stop_machine(cancel_job=False, wait=False)

        if wait:
            self.join()

    def join(self):
        for machine in self.known_machines:
            machine.join()
        super().join()

    def run(self):
        # Make sure the config file exists
        Path(config.MARS_DB_FILE).touch(exist_ok=True)

        # Set up a watch
        inotify = INotify()
        watch_flags = flags.CREATE | flags.DELETE | flags.MODIFY | flags.DELETE_SELF
        inotify.add_watch(config.MARS_DB_FILE, watch_flags)

        # Now wait for changes to the file
        last_sync = None
        while not self.stop_event.is_set():
            try:
                reason = None
                if last_sync is None:
                    reason = "Initial boot"
                elif len(inotify.read(timeout=1000)) > 0:
                    reason = "Got updated on disk"
                elif datetime.now() - last_sync > timedelta(minutes=30):
                    reason = "Periodic check"

                if reason:
                    logger.info(f"Syncing the MaRS DB. Reason: {reason}")

                    self.sync_machines()
                    last_sync = datetime.now()
            except Exception:
                logger.info(traceback.format_exc())
                logger.info("Trying again in 60 seconds")
                time.sleep(60)
