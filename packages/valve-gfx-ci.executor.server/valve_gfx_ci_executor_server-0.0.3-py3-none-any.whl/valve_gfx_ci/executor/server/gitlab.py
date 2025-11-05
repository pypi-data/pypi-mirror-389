from dataclasses import dataclass
from enum import StrEnum
from jinja2 import Template
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import TYPE_CHECKING
import requests
import math
import os
import pathlib
import platform
import psutil


from .logger import logger
from .job_source import JobSourceExternalCommand
from . import config

if TYPE_CHECKING:
    from .mars import ConfigAcl

ACL_SCRIPT_FOLDER = "/usr/local/bin/gitlab-runner-access-control"


def _requests_session(retry: Retry = Retry(total=5, backoff_factor=1,
                                           status_forcelist=[429, 500, 502, 503, 504])) -> requests.Session:
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))

    return session


requests_session = _requests_session()


class SanitizedFieldsMixin:
    @classmethod
    def from_api(cls, fields, **kwargs):
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}

        sanitized_kwargs = dict(fields)
        for arg in fields:
            if arg not in valid_fields:
                sanitized_kwargs.pop(arg)

        return cls(**sanitized_kwargs, **kwargs)


@dataclass
class GitlabRunnerRegistration(SanitizedFieldsMixin):
    id: int
    token: str


class RunnerType(StrEnum):
    INSTANCE = "instance_type"
    GROUP = "group_type"
    PROJECT = "project_type"


@dataclass
class Runner(SanitizedFieldsMixin):
    id: int
    description: str
    active: bool
    paused: bool
    online: bool
    tag_list: list[str]
    maximum_timeout: int


def register_runner(gitlab_url: str, registration_token: str,
                    description: str, tag_list: list[str],
                    run_untagged: bool = False, maximum_timeout: int = 3600,
                    runner_type: RunnerType = RunnerType.INSTANCE,
                    group_id: int = None, project_id: int = None):
    # Make sure the group or project id is set when needed by the runner type
    assert runner_type in RunnerType
    assert runner_type != RunnerType.GROUP or group_id is not None
    assert runner_type != RunnerType.PROJECT or project_id is not None

    params = {
        "description": description,
        "tag_list": ",".join(tag_list),
        "run_untagged": run_untagged,
        "maximum_timeout": maximum_timeout,
        "runner_type": runner_type,
    }

    if group_id:
        params["group_id"] = group_id
    if project_id:
        params["project_id"] = project_id

    r = requests_session.post(f"{gitlab_url}/api/v4/user/runners",
                              headers={"PRIVATE-TOKEN": registration_token}, params=params)
    if r.status_code == 201:
        return GitlabRunnerRegistration.from_api(r.json())
    else:
        return None


def unregister_runner(gitlab_url: str, token: str):
    r = requests_session.delete(f"{gitlab_url}/api/v4/runners", params={"token": token})
    return r.status_code == 204


def verify_runner_token(gitlab_url: str, token: str):
    # WARNING: The interface for this function is so that we will return
    # False *ONLY* when Gitlab tells us the token is invalid.
    # If Gitlab is unreachable, we will return True.
    #
    # This is a conscious decision, as we never want to throw away a perfectly-good
    # token, just because of a network outtage.

    r = requests_session.post(f"{gitlab_url}/api/v4/runners/verify", params={"token": token})
    return not r.status_code == 403


def runner_details(gitlab_url: str, private_token: str, runner_id: int):
    r = requests_session.get(f"{gitlab_url}/api/v4/runners/{runner_id}",
                             headers={"PRIVATE-TOKEN": private_token})
    if r.status_code == 200:
        return Runner.from_api(r.json())
    else:
        return None


def generate_gateway_runner_tags(gateway_runner):
    def next_power_of_2(x):
        return 1 if x == 0 else 2**math.ceil(math.log2(x))

    tags = {f"{config.FARM_NAME}-gateway", 'CI-gateway', f"cpu:arch:{platform.machine()}"}

    cpu_count = psutil.cpu_count(logical=False)
    tags.add(f"cpu:cores:{cpu_count}")
    if cpu_count >= 8:
        tags.add("cpu:cores:8+")
    if cpu_count >= 16:
        tags.add("cpu:cores:16+")
    if cpu_count >= 32:
        tags.add("cpu:cores:32+")

    mem_gib = next_power_of_2(psutil.virtual_memory().total / 1024 / 1024 / 1024)
    tags.add(f"mem:size:{mem_gib}GiB")
    if mem_gib >= 8:
        tags.add("mem:size:8+GiB")
    if mem_gib >= 32:
        tags.add("mem:size:32+GiB")

    tags.update(gateway_runner.acl.allow.tags(prefix='ci-tron:gateway'))

    return tags


def generate_gateway_runner_config(mars_db):
    logger.info("Generate the GitLab runner configuration")
    with open(config.GITLAB_CONF_TEMPLATE_FILE) as f:
        params = {
            "config": config,
            "mars_db": mars_db,
            "cpu_count": psutil.cpu_count(),
            "ram_total_MB": psutil.virtual_memory().total / 1e6
        }
        config_toml = Template(f.read()).render(**params)

    with open(config.GITLAB_CONF_FILE, 'w') as f:
        f.write(config_toml)


def load_access_control_template() -> Template:
    # Load gitlab-runner `pre_build_script` template
    acl_script_template_path = pathlib.Path(config.template('gitlab_runner_access_control.sh.j2'))
    return Template(acl_script_template_path.read_text())


def write_access_control_script(template: Template, gl_name: str, dut_id: str | None, acls: list['ConfigAcl']) -> str:
    script_prefix = f"instance-{gl_name}"
    if dut_id is None:
        script_suffix = "gateway"
    else:
        script_suffix = f"dut-{dut_id.replace(':', '-')}"

    script_path = f"{ACL_SCRIPT_FOLDER}/{script_prefix}-{script_suffix}.sh"
    with open(script_path, 'w') as f:
        f.write(template.render(acls=acls))

    # Current user (writing this script) is `executor:executor`,
    # and we also want `gitlab-runner:gitlab-runner` to execute it.
    # Note: we are unable to set the group to `gitlab-runner`,
    # so instead we allow "others" to read & execute this script.
    # The folder's permissions already limit to only
    # `executor:gitlab-runner` (0 for others), in practice this
    # doesn't change anything.
    os.chmod(script_path, 0o205)

    return script_path


@dataclass
class GitlabJobSource(JobSourceExternalCommand):
    JOB_SOURCE_NAME = "Gitlab"
    JOB_PICKUP_TIMEOUT_SECONDS = 0

    def _subprocess_kwargs(self) -> dict[str, str]:
        # Get the ACL associated to the priority queue of the DUT for the job source
        dut_job_src_queue_acl = self.db_dut.gitlab.get(self.job_src.name).acl

        # Get the ACL associated to the priority queue of the whole job source instance
        job_src_queue_acl = None
        if exposed_priorities := self.job_src.exposed_priorities:
            if settings := exposed_priorities.get(self.db_dut_job_src.priority, None):
                job_src_queue_acl = settings.acl

        # Convert the DUT runner's ACL to a gitlab-runner `pre_build_script`
        acl_script_path = write_access_control_script(template=load_access_control_template(),
                                                      gl_name=self.job_src.name, dut_id=self.db_dut.id,
                                                      acls=[dut_job_src_queue_acl, self.db_dut_job_src.acl,
                                                            job_src_queue_acl, self.job_src.acl])

        run_single_command = [
            config.GITLAB_RUNNER_PATH,
            "run-single",
            "--max-builds", "1",
            "--wait-timeout", "1",
            "--limit", "1",
            "--name", self.db_dut.full_name,
            "--url", self.job_src.url,
            "--token", self.db_dut_job_src.token,
            "--executor", "docker",
            "--docker-network-mode", "host",
            "--docker-shm-size", "0",
            "--docker-cpus", "1",
            "--docker-memory", "1GB",
            "--docker-memory-swap", "1GB",
            "--docker-memory-reservation", "512MB",
            "--docker-volumes", f"{acl_script_path}:/access_control",
            "--pre-build-script", "/access_control",
            "--env", f"CI_TRON_JOB_COOKIE={self.job_cookie}",
        ]

        for k, v in config.job_environment_vars().items():
            run_single_command.extend(["--env", f"{k}={v}"])

        return {"args": run_single_command}
