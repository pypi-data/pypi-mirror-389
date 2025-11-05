from dataclasses import fields, field, asdict, InitVar
from datetime import datetime, timedelta
from collections import defaultdict
from copy import deepcopy
from pydantic.dataclasses import dataclass
from pydantic.functional_validators import AfterValidator
from pydantic import field_validator, model_validator, PositiveInt, NonNegativeInt, BaseModel, Field, HttpUrl
from typing import Annotated, Any, Generic, TypeVar, get_args
from urllib.parse import urlparse
from jinja2 import Template, ChainableUndefined
import traceback
import yaml
import sys
import re

from .dhcpd import BootProtocol, CPUArch, DhcpRequest, Firmware, DhcpOptions, DhcpOption, DhcpOptionValue
from .dhcpd import MacAddress as _MacAddress
from .artifact.uimage import UImageFormatCompression, UImageFormatOS, UImageFormatType, UImageArtifact
from .artifact.archive import ArchiveArtifact, ArchiveFormat, ArchiveCompression, ArtifactKeep, ArtifactAdd
from .artifact import ArtifactIOBase, DataArtifact, HttpArtifactCache
from .imagestore import ImageStoreImage, ImageStorePullPolicy, imagestore_template_resources
from .registry import registry_template_resources
from . import config, nbd


default_artifact_cache = HttpArtifactCache(cache_root=config.EXECUTOR_ARTIFACT_CACHE_ROOT,
                                           log_callback=sys.stderr.write, start_bg_validation=True)


@dataclass(config=dict(extra="forbid"))
class Target:
    id: str | None = None
    tags: list[str] | None = None

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent and field validation succeeded
    def __post_init__(self):
        if not self.id and self.tags is None:
            raise ValueError("The target is neither identified by tags or id. "
                             "Use empty tags to mean 'any machines'.")

        if self.tags is None:
            self.tags = []

    def __str__(self):
        return f"<Target: id={self.id}, tags={self.tags}>"


@dataclass(config=dict(extra="forbid"))
class Timeout:
    days: float | None = None
    hours: float | None = None
    minutes: float | None = None
    seconds: float | None = None
    milliseconds: float | None = None
    retries: NonNegativeInt = 0

    @classmethod
    def create(cls, name, *args, **kwargs):
        timeout = cls(*args, **kwargs)
        timeout.name = name
        return timeout

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent and field validation succeeded
    def __post_init__(self):
        days = self.days or 0
        hours = self.hours or 0
        minutes = self.minutes or 0
        seconds = self.seconds or 0
        milliseconds = self.milliseconds or 0

        self.timeout = timedelta(days=days, hours=hours,
                                 minutes=minutes, seconds=seconds,
                                 milliseconds=milliseconds)

        if (self.days is None and self.hours is None and self.minutes is None and
                self.seconds is None and self.milliseconds is None):
            self.timeout = timedelta.max

        self.started_at = None
        self.retried = 0

    @property
    def active_for(self):
        if self.started_at is not None:
            return datetime.now() - self.started_at
        else:
            return None

    @property
    def is_started(self):
        return self.started_at is not None

    @property
    def has_expired(self):
        active_for = self.active_for
        return active_for is not None and active_for > self.timeout

    @property
    def remaining_time(self) -> timedelta:
        return self.timeout - (self.active_for or timedelta())

    def start(self):
        self.started_at = datetime.now()

    def reset(self, when=None):
        if when is None:
            when = datetime.now()
        self.started_at = when

    def retry(self):
        self.stop()
        self.retried += 1

        return self.retried <= self.retries

    def stop(self):
        self.started_at = None

    def __str__(self):
        return f"<Timeout {self.name}: value={self.timeout}, retries={self.retried}/{self.retries}>"


@dataclass(config=dict(extra="forbid"))
class Timeouts:
    # Maximum time the job can take, not overrideable by the "continue" deployment
    overall: Timeout = field(default_factory=lambda: Timeout(hours=6))

    # Maximum time to download the job artifacts, such as kernel & initramfs
    infra_setup: Timeout = field(default_factory=Timeout)

    # Maximum time to wait for the job bucket to be downloaded back to the gateway
    infra_teardown: Timeout = field(default_factory=Timeout)

    # Maximum time the machine can remain on
    boot_cycle: Timeout = field(default_factory=Timeout)

    # Maximum time after the last console log message until the machine is considered as hung and needing to be rebooted
    console_activity: Timeout = field(default_factory=Timeout)

    # Maximum time until we receive the first console log after a (re)boot
    first_console_activity: Timeout = field(default_factory=Timeout)

    # Maximum time the firmware can take before the boot process starts (DHCP request, fastboot, ...)
    firmware_boot: Timeout = field(default_factory=Timeout)

    watchdogs: dict[str, Timeout] = field(default_factory=dict)

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent and field validation succeeded
    def __post_init__(self):
        # Set a sane default timeout, 25% of overall timeout, for the infra setup and teardown timeouts
        if self.infra_setup == Timeout():
            self.infra_setup = Timeout(seconds=self.overall.timeout.seconds / 4)
        if self.infra_teardown == Timeout():
            self.infra_teardown = Timeout(seconds=self.overall.timeout.seconds / 4)

        # Make sure to add the name to every field
        for f in fields(self):
            if f.type is Timeout:
                getattr(self, f.name).name = f.name

        # Add the watchdogs' names
        for name, wd in self.watchdogs.items():
            wd.name = name

        # Ensure that the overall and tear-down timeouts have retries=0
        for timeout in [self.overall, self.infra_teardown]:
            if timeout.retries != 0:
                raise ValueError("Neither the overall nor the teardown timeout can have retries")

    def __iter__(self):
        for f in fields(self):
            if f.type is Timeout:
                yield getattr(self, f.name)

        for wd in self.watchdogs.values():
            yield wd

    @property
    def expired_list(self):
        expired = []
        for timeout in self:
            if timeout.has_expired:
                expired.append(timeout)
        return expired

    @property
    def has_expired(self):
        return len(self.expired_list) > 0


@dataclass(config=dict(extra="forbid"))
class Pattern:
    regex: str

    @field_validator("regex")
    @classmethod
    def convert_to_regex(cls, v):
        try:
            return re.compile(v.encode())
        except re.error as e:
            raise ValueError(f"Console pattern '{v}' is not a valid regular expression: {e.msg}")

    def __str__(self):
        return f"{self.regex.pattern}"


@dataclass(config=dict(extra="forbid"))
class Watchdog:
    start: Pattern
    reset: Pattern
    stop: Pattern

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent and field validation succeeded
    def __post_init__(self):
        self.timeout = None

    def set_timeout(self, timeout):
        self.timeout = timeout

    def process_line(self, line):
        # Do not parse lines if no timeout is associated
        if self.timeout is None:
            return {}

        if not self.timeout.is_started:
            if self.start.regex.search(line):
                self.timeout.start()
                return {"start"}
        else:
            if self.reset.regex.search(line):
                self.timeout.reset()
                return {"reset"}
            elif self.stop.regex.search(line):
                self.timeout.stop()
                return {"stop"}

        return {}

    # I would have loved to re-use `stop()` here, but it collides with the stop pattern
    def cancel(self):
        if self.timeout is not None:
            self.timeout.stop()


@dataclass(config=dict(extra="forbid"))
class ConsoleState:
    session_end: Pattern = field(default_factory=lambda: Pattern(regex=r"^\[[\d \.]{12}\] reboot: Power Down$"))
    session_reboot: Pattern | None = None
    job_success: Pattern | None = None
    job_warn: Pattern | None = None
    machine_unfit_for_service: Pattern | None = None
    watchdogs: dict[str, Watchdog] = field(default_factory=dict)

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent and field validation succeeded
    def __post_init__(self):
        self._patterns = dict()
        self._matched = set()

        if self.machine_unfit_for_service is None and config.CONSOLE_PATTERN_DEFAULT_MACHINE_UNFIT_FOR_SERVICE_REGEX:
            self.machine_unfit_for_service = Pattern(config.CONSOLE_PATTERN_DEFAULT_MACHINE_UNFIT_FOR_SERVICE_REGEX)

        # Generate the list of patterns to match
        for f in fields(self):
            if f.type in [Pattern, Pattern | None]:
                pattern = getattr(self, f.name, None)
                if pattern:
                    pattern.name = f.name
                    self._patterns[f.name] = pattern

    def process_line(self, line):
        # Try matching all the patterns
        matched = set()
        for name, pattern in self._patterns.items():
            if pattern.regex.search(line):
                matched.add(name)
        self._matched.update(matched)

        # Try matching the watchdogs
        for name, wd in self.watchdogs.items():
            _matched = wd.process_line(line)
            matched.update({f"{name}.{m}" for m in _matched})

        return matched

    def reset_per_boot_state(self):
        self._matched.discard("session_reboot")

    @property
    def session_has_ended(self):
        return "session_end" in self._matched or "unfit_for_service" in self._matched

    @property
    def needs_reboot(self):
        return "session_reboot" in self._matched

    @property
    def machine_is_unfit_for_service(self):
        return "machine_unfit_for_service" in self._matched

    @property
    def job_status(self):
        if "session_end" not in self._matched:
            return "INCOMPLETE"

        if "job_success" in self._patterns:
            if "job_success" in self._matched:
                if "job_warn" in self._matched:
                    return "WARN"
                else:
                    return "PASS"
            else:
                return "FAIL"
        else:
            return "COMPLETE"


class DeploymentMixin:
    def update(self, d):
        # Nothing to do if `d` is empty
        if not d:
            return self

        # Convert `d` from dict to the proper instance if needed
        if type(d) is dict:
            d = type(self)(**d)

        # Assert that both `self` and `d` share the same type
        assert type(d) is type(self)

        # Check every field
        for f in fields(self):
            if new := getattr(d, f.name, None):
                # If the value was already set and the new value is a DeploymentMixin, call `update()` rather than
                # simply copying
                if cur := getattr(self, f.name):
                    if isinstance(cur, DeploymentMixin):
                        cur.update(new)
                        continue
                    elif isinstance(cur, dict):
                        for name in new:
                            if name in cur and isinstance(cur[name], DeploymentMixin):
                                cur[name].update(new[name])
                            else:
                                cur[name] = new[name]
                        continue

                setattr(self, f.name, deepcopy(new))

        return self

    @classmethod
    def _add_artifacts_from_object(cls, artifacts, obj_name, obj):
        for url, paths in obj.artifacts.items():
            for path, artifact in paths.items():
                artifacts[url][(obj_name, ) + path] = artifact

    @property
    def artifacts(self):
        if hasattr(self, "url"):
            url = str(self.url) if self.url else None
            return {url: {(): self}}

        artifacts = defaultdict(dict)

        for f in fields(self):
            if f_value := getattr(self, f.name, None):
                if isinstance(f_value, DeploymentMixin):
                    self._add_artifacts_from_object(artifacts, f.name, f_value)

        return artifacts

    def __str__(self):
        """Returns a string containing only the non-default field values."""
        fields_set = []
        for f in fields(self):
            if getattr(self, f.name) != f.default:
                fields_set.append(f'{f.name}={getattr(self, f.name)!s}')
        return f'{type(self).__name__}({', '.join(fields_set)})'


T = TypeVar("T")


def as_list(v):
    if isinstance(v, list):
        return v
    else:
        return [v]


SingleItemOrList = Annotated[T | list[T], AfterValidator(lambda v: as_list(v))]


def is_valid_category_name(v: str, allow_keywords=False) -> str:
    if v[0] == ":":
        if not allow_keywords or v not in [":uncategorised"]:
            raise ValueError("User-defined category names cannot start with ':'")
    return v


Category = Annotated[str, AfterValidator(lambda v: is_valid_category_name(v, allow_keywords=False))]


CategoryOrKeyword = Annotated[str, AfterValidator(lambda v: is_valid_category_name(v, allow_keywords=True))]


JobCollectionOfLists = SingleItemOrList | dict[CategoryOrKeyword, SingleItemOrList]


@dataclass(config=dict(extra="forbid"))
class CollectionOfLists(Generic[T], DeploymentMixin):
    categories: dict[Category, list[T] | None] | None = field(default_factory=dict)
    uncategorised: list[T] | None = field(default_factory=list)

    def __post_init__(self):
        for category in self.categories:
            if self.categories[category] is None:
                self.categories[category] = []

        if self.uncategorised is None:
            self.uncategorised = []

    @property
    def as_list(self) -> list[T]:
        # NOTE: We are sorting the categories by names to let users order how elements are staged
        cl = []
        if self.categories:
            for k in sorted(self.categories.keys()):
                cl.extend(self.categories[k])

        if self.uncategorised:
            cl.extend(self.uncategorised)

        return cl

    def update(self, d: "CollectionOfLists"):
        assert isinstance(d, CollectionOfLists)

        if d.categories:
            self.categories.update(d.categories)

        if d.uncategorised and len(d.uncategorised) > 0:
            self.uncategorised = d.uncategorised

        return self

    @property
    def artifacts(self):
        artifacts = defaultdict(dict)

        # Add every element from the list
        for i, element in enumerate(self):
            if isinstance(element, DeploymentMixin):
                self._add_artifacts_from_object(artifacts, str(i), element)

        return artifacts

    def __str__(self):
        return " ".join([str(v) for v in self.as_list])

    def __eq__(self, other: "CollectionOfLists"):
        if isinstance(other, str):
            return str(self) == other
        else:
            for f in fields(self):
                if getattr(self, f.name, None) != getattr(other, f.name, None):
                    return False

            return True

    def __iter__(self):
        return iter(self.as_list)

    def __getitem__(self, key):
        return self.as_list[key]

    def __len__(self):
        return len(self.as_list)

    @classmethod
    def from_job(cls, v: "CollectionOfLists" | JobCollectionOfLists):
        categories = dict()
        uncategorised = []
        if isinstance(v, cls):
            return v
        elif isinstance(v, dict):
            uncategorised = v.pop(":uncategorised", [])
            for key, value in v.items():
                categories[key] = as_list(value)
        else:
            uncategorised = as_list(v)

        return cls(categories=categories, uncategorised=uncategorised)


ComplexList = Annotated[JobCollectionOfLists, AfterValidator(CollectionOfLists.from_job)] | CollectionOfLists[T]


def compile_re(v):
    try:
        return re.compile(v)
    except re.error as e:
        raise ValueError(str(e))


Regex = Annotated[str, AfterValidator(compile_re)]


def ensure_is_valid_regex(v):
    try:
        re.compile(v)
        return v
    except re.error as e:
        raise ValueError(str(e))


RegexAsStr = Annotated[str, AfterValidator(ensure_is_valid_regex)]


def split_host_port(host_port: str) -> tuple[str, int]:
    host, port = host_port.rsplit(":", maxsplit=1)

    # Handle IPv6
    if host.startswith("[") != host.endswith("]"):
        raise ValueError("ipv6 is invalid")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:][:-1]
    elif ":" in host:
        raise ValueError("ipv6 must be wrapped in [...]")

    port = int(port)
    if port < 1 or port > 65535:
        raise ValueError("port number out of 1-65535 range")

    return host, port


def ensure_is_valid_host_port(v):
    try:
        split_host_port(v)
        return v
    except Exception as e:
        raise ValueError(f"Malformed endpoint. Expected `host:port`. Error: {str(e)}")


NetworkEndpoint = Annotated[str, AfterValidator(ensure_is_valid_host_port)]


@dataclass(config=dict(extra="forbid"))
class UBootArtifactFormatDeployment(DeploymentMixin):
    architecture: CPUArch | None = CPUArch.ARM64
    compression: UImageFormatCompression | None = UImageFormatCompression.NONE
    os: UImageFormatOS | None = UImageFormatOS.LINUX
    type: UImageFormatType | None = UImageFormatType.SCRIPT

    def format(self, job_artifact: "ArtifactDeployment", artifact: ArtifactIOBase, path: str,
               polling_delay: float = 0.05, artifact_cache: HttpArtifactCache | None = None) -> ArtifactIOBase:
        return UImageArtifact(artifact=artifact, architecture=self.architecture,
                              compression=self.compression, os=self.os, type=self.type)


@dataclass(config=dict(extra="forbid"))
class ArtifactArchiveAddArtifact(DeploymentMixin):
    path: str
    artifact: "ArtifactDeployment"
    mode: int = 0o100644

    def to_artifact_add(self, job_artifact_path: str, request_path: str, polling_delay: float = 0.05,
                        artifact_cache: HttpArtifactCache | None = None) -> ArtifactAdd:
        # Try rewriting the path based on the job artifact's path, which is
        # useful when wanting to create a file at a location based on the
        # request path we got
        add_path = None
        if job_artifact_path:
            try:
                add_path = re.sub(f"^{job_artifact_path}$", self.path, request_path)
                if add_path == request_path:
                    # The wanted path does not match the artifact path, which indicates that
                    # artifact_path wasn't a regex and we should thus use self.path verbatim
                    add_path = self.path
            except re.error:
                # The rewriting is not possible, use self.path verbatim
                pass

        if not add_path:
            add_path = self.path

        return ArtifactAdd(artifact=self.artifact.open(path=f"{request_path}-{add_path}", polling_delay=polling_delay,
                                                       artifact_cache=artifact_cache),
                           path=add_path, mode=self.mode)


@dataclass(config=dict(extra="forbid"))
class ArtifactArchiveDeployment(DeploymentMixin):
    extension: ArchiveFormat | None = None
    compression: ArchiveCompression | None = ArchiveCompression.NONE
    add: list[ArtifactArchiveAddArtifact] | None = field(default_factory=list)


@dataclass(config=dict(extra="forbid"))
class ArtifactArchiveFormatKeep(DeploymentMixin):
    path: str
    rewrite: str | None = None

    def to_artifact_keep(self, job_artifact_path: str, request_path: str):
        keep_path = self.path

        # Try rewriting the path based on the job artifact's path, which is
        # useful when looking for a specific file inside the archive based on
        # the request path we got (think find a dtb file in the archive as
        # asked through TFTP)
        if job_artifact_path:
            try:
                keep_path = re.sub(f"^{job_artifact_path}$", self.path, request_path)
                if keep_path == request_path:
                    # The wanted path does not match the artifact path, which indicates that
                    # artifact_path wasn't a regex and we should thus use self.path verbatim
                    keep_path = self.path
            except re.error:
                # The rewriting is not possible, use self.path verbatim
                pass

        return ArtifactKeep(path=re.compile(keep_path), rewrite=self.rewrite)


@dataclass(config=dict(extra="forbid"))
class ArtifactArchiveFormatDeployment(ArtifactArchiveDeployment):
    keep: list[ArtifactArchiveFormatKeep] | None = field(default_factory=list)

    # Helpers
    match: InitVar[str | None] = None

    def __post_init__(self, match: str):
        if match:
            if len(self.keep) > 0:
                raise ValueError("The `match` is incompatible with `keep`")
            elif len(self.add) > 0:
                raise ValueError("The `match` is incompatible with `add`")

            self.extension = ArchiveFormat.NONE
            self.compression = ArchiveCompression.NONE
            self.keep = [ArtifactArchiveFormatKeep(path=match)]

    def format(self, job_artifact: "ArtifactDeployment", artifact: ArtifactIOBase, request_path: str,
               polling_delay: float = 0.05, artifact_cache: HttpArtifactCache | None = None) -> ArtifactIOBase:
        artifact_path = getattr(job_artifact, "path", None)
        rewritten_keep = [k.to_artifact_keep(artifact_path, request_path) for k in self.keep]
        rewritten_add = [a.to_artifact_add(artifact_path, request_path, polling_delay=polling_delay,
                                           artifact_cache=artifact_cache) for a in self.add]

        return ArchiveArtifact(artifact=artifact, format=self.extension, keep=rewritten_keep,
                               compression=self.compression, add=rewritten_add)


@dataclass(config=dict(extra="forbid"))
class ArtifactFormatDeployment(DeploymentMixin):
    uboot: UBootArtifactFormatDeployment | None = None
    archive: ArtifactArchiveFormatDeployment | None = None

    def format(self, *args, **kwargs) -> ArtifactIOBase:
        for f in fields(self):
            if fmt := getattr(self, f.name, None):
                return fmt.format(*args, **kwargs)


def ensure_the_url_is_valid(v):
    if v:
        # Remove any spaces around the URL
        v = v.strip()

        url = HttpUrl(v)
        if url.scheme not in ["http", "https"]:  # pragma: nocover
            raise ValueError("Unsupported schema")
        elif str(url) != v:
            raise ValueError("The URL is malformed")
    return v


StrHttpUrl = Annotated[str, AfterValidator(ensure_the_url_is_valid)]


@dataclass(config=dict(extra="forbid"))
class ArtifactDeployment(DeploymentMixin):
    url: str | None = None
    data: str | bytes | None = None
    archive: ArtifactArchiveDeployment | None = None
    format: SingleItemOrList[ArtifactFormatDeployment] | None = None

    @field_validator("url")
    @classmethod
    def ensure_the_url_is_valid(cls, v):
        return ensure_the_url_is_valid(v)

    @model_validator(mode='after')
    def check_only_one_source_is_set(self):
        source_found = False
        for src_field in ['archive', 'data', 'url']:
            if getattr(self, src_field, None):
                if source_found:
                    raise ValueError("Can only set one artifact source: 'archive', 'data', or 'url'")
                else:
                    source_found = True
        return self

    @property
    def has_dynamic_url(self):
        # Return True if the URL set by the job uses URL rewriting. This is only applicable to StorageArtifactDeployment
        return False

    @classmethod
    def render_data_template(cls, artifact_cache: HttpArtifactCache | None, data: str | bytes,
                             template_params: dict = None):
        # Templates only work on strings, so return the raw data otherwise
        if not isinstance(data, str):
            return data

        if not template_params:
            if artifact_cache and hasattr(artifact_cache, "common_template_resources"):  # pragma: nocover
                template_params = artifact_cache.common_template_resources
            else:
                template_params = Job.common_template_resources()

        ignore_jinja_errors = True
        jinja_prefix = '#!jinja2\n'
        if data.startswith(jinja_prefix):
            data = data.removeprefix(jinja_prefix)
            ignore_jinja_errors = False

        # TODO: when bumping the job template version, merge the `return Template().render()` into
        # the `if` above and put the `return data` as the `else`, dropping the `try/except` below.
        try:
            return Template(data, undefined=ChainableUndefined, keep_trailing_newline=True).render(**template_params)
        except Exception:
            if not ignore_jinja_errors:
                raise
            return data

    def open(self, path: str, polling_delay: float = 0.05,
             artifact_cache: HttpArtifactCache | None = None) -> ArtifactIOBase:
        if artifact_cache is None:
            artifact_cache = default_artifact_cache

        # Get the artifact's path, as defined in StorageArtifactDeployment if applicable
        # NOTE: This enables rewriting URLs and values
        artifact_path = getattr(self, "path", None)

        if self.data is not None:
            artifact = DataArtifact(self.render_data_template(artifact_cache, self.data))
        elif self.archive:
            # NOTE: We ArchiveArtifacts cannot have "keep" attributes because they do not have any source artifact
            # to keep files from
            artifact = ArchiveArtifact(artifact=None, format=self.archive.extension,
                                       compression=self.archive.compression,
                                       add=[a.to_artifact_add(artifact_path, path, polling_delay=polling_delay,
                                            artifact_cache=artifact_cache) for a in self.archive.add])
        else:
            # Handle URL rewriting
            if artifact_path:
                url = re.sub(f"^{artifact_path}$", self.url, path)
                if url == path:
                    # The wanted path does not match the artifact path, which indicates that
                    # artifact_path wasn't a regex and we should thus use self.url verbatim
                    url = self.url
            else:
                url = self.url

            instance = artifact_cache.get_or_reuse_instance(url=url, name=path)
            artifact = instance.open(polling_delay=polling_delay)

        # Format the artifact, if asked to
        if self.format:
            for fmt in self.format:
                artifact = fmt.format(self, artifact, path)

        return artifact


@dataclass(config=dict(extra="forbid"))
class StorageArtifactDeployment(ArtifactDeployment):
    path: str | None = None

    # Proposals:
    # args: dict[str, str] | None = None  # Only match when the following GET params are set

    @model_validator(mode='after')
    def ensure_path_is_set_and_valid(self):
        if not self.path:
            raise ValueError("Cannot be empty")

        if not self.path.startswith("/"):
            raise ValueError("Needs to be absolute")

        if self.path.startswith("/_/"):
            raise ValueError("Reserved path")

        return self

    @field_validator("url")
    @classmethod
    def ensure_the_url_is_valid(cls, v):
        # Override the original url validator and always return the raw value
        if v:
            return v.strip()

    @model_validator(mode='after')
    def final_url_validation(self):
        self._has_dynamic_url = False
        if self.data is None:
            try:
                super().ensure_the_url_is_valid(self.url)
            except Exception:
                # The Http URL is not valid directly, let's try as a regular expression instead!
                try:
                    re.sub(f"^{self.path}$", self.url, "")
                    self._has_dynamic_url = True
                except Exception:
                    raise ValueError("The `url` parameter is neither a valid HTTP URL nor a valid regex")

        return self

    @property
    def has_dynamic_url(self):
        return self._has_dynamic_url

    def matches(self, path: str) -> (bool | re.Match):
        if str(path) == str(self.path):
            return True

        # Try considering the URL as a regular expression
        if m := re.fullmatch(self.path, path):
            return m

        return False


def assert_is_valid_image_name(v):
    # Remove any potential whitespace before or after the image name
    v = v.strip()

    # Assert that no space is found in the image name as it may contain additional commands
    if " " in v or "\t" in v:
        raise ValueError("No whitespace accepted in image names")

    # Try to parse the string as a url and check a couple of fields
    url = urlparse(v)

    # Ensure no parameters are set, since they are not allowed in images
    if url.params != "" or url.query != "" or url.fragment != "":
        raise ValueError("No parameters, query parameters, or fragments are supported")

    # Support image names of the form "alpine:latest" by considering alpine as being the path not the scheme
    if url.netloc == "" and url.scheme != "":
        return v
    elif url.scheme not in ["", "docker"]:
        raise ValueError(f"Unsupported scheme '{url.scheme}'")

    return v


ContainerImageName = Annotated[str, AfterValidator(assert_is_valid_image_name)]


@dataclass(config=dict(extra="forbid"))
class ContainerImageStorage(DeploymentMixin):
    name: ContainerImageName
    tls_verify: bool = True
    platform: str = "linux/amd64"
    pull: ImageStorePullPolicy = ImageStorePullPolicy.RELAXED_ALWAYS


def assert_is_valid_resource_name(v):
    if not re.fullmatch(r"\w+", v):
        raise ValueError("A resource name should only be constituted of alphanumeric characters, or underscores")

    return v


ResourceName = Annotated[str, AfterValidator(assert_is_valid_resource_name)]


@dataclass(config=dict(extra="forbid"))
class ImageStoreStorage(DeploymentMixin):
    images: dict[ResourceName, ContainerImageStorage] | None = field(default_factory=list)

    @field_validator("images")
    @classmethod
    def ensure_images_is_a_dict(cls, v):
        if v is None:
            return {}
        else:
            return v


def assert_is_valid_imagestore_name(v):
    if v != "public":
        raise ValueError(f"Unsupported imagestore name `{v}`: Only `public` is accepted")

    return v


ImageStoreName = Annotated[str, AfterValidator(assert_is_valid_imagestore_name)]


def convert_human_size_to_bytes(v: str):
    exponents = ["k", "M", "G", "T", "P"]

    if m := re.fullmatch(r"(?P<number>\d+)(?P<exponent>[kMGTP])?(?P<base>i?B?)", v):
        groups = m.groupdict()

        number = int(groups['number'])
        base = 1000 if groups.get('base') == 'B' else 1024

        if groups.get('exponent'):
            exponent = exponents.index(groups['exponent']) + 1
        else:
            exponent = 0

        return number * base ** exponent

    raise ValueError(f"Invalid size argument '{v}'. Expected format: 1k, 2MiB, or 3GB")


HumanSize = PositiveInt | Annotated[str, AfterValidator(convert_human_size_to_bytes)]


@dataclass(config=dict(extra="forbid"))
class NbdStorage(DeploymentMixin):
    readonly: bool = False
    max_connections: PositiveInt = 4
    # TODO: Add support for persistance, so that,for example, volumes may be shared between jobs

    url: StrHttpUrl | None = None
    size: HumanSize | None = None

    @model_validator(mode='after')
    def ensure_only_one_mode_is_used(self):
        if self.url and self.size:
            raise ValueError("Only one backing may be selected at a time")
        elif not self.url and not self.size:
            raise ValueError("No backing were selected")

        return self

    def setup(self, name: str, polling_delay: float = 0.05, artifact_cache: HttpArtifactCache | None = None,
              timeout: float = None) -> nbd.Nbd:
        if self.url:
            if artifact_cache is None:  # pragma: nocover
                artifact_cache = default_artifact_cache

            instance = artifact_cache.get_or_reuse_instance(url=self.url, name=name)
            backing = instance.get_filepath(polling_delay=polling_delay)
            backing_read_only = True
        elif self.size:
            backing = nbd.create_tmp_raw_backing(self.size)
            backing_read_only = False

        ret = nbd.Nbd(name=name, backing=backing, backing_read_only=backing_read_only,
                      export_as_read_only=self.readonly, max_connections=self.max_connections)
        ret.setup(timeout=timeout)
        return ret


@dataclass(config=dict(extra="forbid"))
class StorageDeployment(DeploymentMixin):
    http: ComplexList[StorageArtifactDeployment] | None = field(default_factory=list)
    tftp: ComplexList[StorageArtifactDeployment] | None = field(default_factory=list)
    imagestore: dict[ImageStoreName, ImageStoreStorage] | None = field(default_factory=dict)
    nbd: dict[ResourceName, NbdStorage] | None = field(default_factory=dict)


@dataclass(config=dict(extra="forbid"))
class FastbootDeployment(DeploymentMixin):
    header_version: int | None = None
    base: int | None = None
    kernel_offset: int | None = None
    ramdisk_offset: int | None = None
    dtb_offset: int | None = None
    tags_offset: int | None = None
    board: str | None = None
    pagesize: int | None = None

    os_version: str | None = None
    os_patch_level: str | None = None

    # A ready-made boot image, bypassing the need to generate the image ourselves
    boot_image: ArtifactDeployment | None = None

    @property
    def fields_set(self):
        return {k: v for k, v in asdict(self).items() if v}

    def __str__(self):
        non_empty_fields = list()
        for key, value in self.fields_set.items():
            # Show some of the fields as hex values, since it is likely what people used
            if key in ["base"] or "_offset" in key:
                value = hex(value)
            non_empty_fields.append(f"{key}={value}")

        s = ", ".join(non_empty_fields)
        return f"<Fastboot: {s}>"


MacAddress = Annotated[str, AfterValidator(lambda v: _MacAddress(v))]


@dataclass(config=dict(extra="forbid"))
class DhcpRequestMatcher:
    # NOTE: All the specified values must be a match to be considered a valid match
    architecture: SingleItemOrList[CPUArch] | None = None
    firmware: SingleItemOrList[Firmware] | None = None
    mac_address: SingleItemOrList[MacAddress | RegexAsStr] | None = None
    protocol: SingleItemOrList[BootProtocol] | None = None
    vendor_class: SingleItemOrList[RegexAsStr | str] | None = None
    user_class: SingleItemOrList[RegexAsStr | str] | None = None
    uuid: SingleItemOrList[RegexAsStr | str] | None = None

    # TODO: raw fields?
    # raw_dhcp_options: dict[int, SingleItemOrList[bytes]] | None = None

    def matches(self, request: DhcpRequest) -> bool:
        def value_matches(field, expected_values):
            request_value = getattr(request, field.name)

            # Try matching the value directly
            if request_value in expected_values:
                return True

            # Try matching the value with regular expressions, converting the request value to a string if RegexAsStr
            # is an accepted type in the field
            if type(request_value) not in [str, bytes] and RegexAsStr in get_args(get_args(get_args(field.type)[0])[0]):
                request_value = str(request_value)

            if type(request_value) in [str, bytes]:
                for expected_value in expected_values:
                    # Only match values of the same type (str <-> str, or bytes <-> bytes)
                    # NOTE: Some expected_values may be non-str/bytes objects (like MacAddress)
                    if type(request_value) is type(expected_value):
                        try:
                            if re.fullmatch(expected_value, request_value):
                                return True
                        except re.error:
                            # The value wasn't a valid regular expression... ignore!
                            pass

            return False

        for f in fields(self):
            if expected_values := getattr(self, f.name, None):
                if not value_matches(f, expected_values):
                    return False

        return True


@dataclass(config=dict(extra="forbid"))
class DhcpDeployment(DeploymentMixin):
    match: DhcpRequestMatcher | None = None
    options: dict[DhcpOption, DhcpOptionValue] | None = field(default_factory=dict)

    @field_validator("options")
    @classmethod
    def ensure_options_are_valid(cls, v):
        return DhcpOptions(v)

    def matches(self, request: DhcpRequest) -> bool:
        return self.match is None or self.match.matches(request)


@dataclass(config=dict(extra="forbid"))
class KernelDeployment(ArtifactDeployment, DeploymentMixin):
    cmdline: ComplexList[str] = None


@dataclass(config=dict(extra="forbid"))
class DeploymentState(DeploymentMixin):
    kernel: KernelDeployment | None = None
    initramfs: ComplexList[ArtifactDeployment] | None = None
    dtb: ComplexList[ArtifactDeployment] | None = None
    storage: StorageDeployment | None = None
    fastboot: FastbootDeployment | None = None
    dhcp: ComplexList[DhcpDeployment] | None = None

    @property
    def container_images(self) -> dict[str, dict[str, ImageStoreImage]]:
        images = defaultdict(dict)
        if self.storage and self.storage.imagestore:
            for store_name, imagestore in self.storage.imagestore.items():
                for i, image_name in enumerate(imagestore.images):
                    image = imagestore.images[image_name]
                    images[store_name][image_name] = ImageStoreImage(store_name=store_name, image_name=image.name,
                                                                     platform=image.platform,
                                                                     tls_verify=image.tls_verify,
                                                                     pull_policy=image.pull)
        return images

    @property
    def nbd_storages(self) -> dict[str, NbdStorage]:
        if self.storage and self.storage.nbd:
            return self.storage.nbd
        else:
            return {}


# NOTE: Because the "continue" field in deployment cannot be used as a dataclass variable,
# we have to open code it using a pydantic BaseModel. Fortunately, pydantic is happy to
# allow us to use an alias for the field.
class Deployment(BaseModel):
    model_config = dict(populate_by_name=True, extra="forbid")

    start: DeploymentState
    continue_: DeploymentState = Field(default=None, alias='continue')

    def __init__(self, /, **data: Any):
        def container_images_to_set(deployment):
            return {(store, name) for store, imgstore in deployment.container_images.items() for name in imgstore}

        super().__init__(**data)

        continue_ = DeploymentState(**asdict(self.start))
        if self.continue_:
            # Ensure the imagestore names are not reused
            common_container_images = container_images_to_set(self.start) & container_images_to_set(self.continue_)
            if len(common_container_images) > 0:
                common_str = ", ".join(sorted([f"{c[0]}/{c[1]}" for c in common_container_images]))
                raise ValueError(f"Can't redefine container images the continue deployment: {common_str}")

            continue_.update(self.continue_)
        self.continue_ = continue_

    @property
    def artifacts(self):
        artifacts = defaultdict(dict)

        DeploymentMixin._add_artifacts_from_object(artifacts, "start", self.start)
        DeploymentMixin._add_artifacts_from_object(artifacts, "continue", self.continue_)

        return artifacts

    @property
    def container_images(self) -> dict[str, dict[str, ImageStoreImage]]:
        # NOTE: The continue state is the aggregation of the sum of the two states, and since we can't have duplicate
        # names it is the superset of the both the start- and continue-provided images
        return self.continue_.container_images

    @property
    def nbd_storages(self) -> dict[str, NbdStorage]:
        # NOTE: The continue state is the aggregation of the sum of the two states, and since we can't have duplicate
        # names it is the superset of the both the start- and continue-provided images
        return self.continue_.nbd_storages


@dataclass(config=dict(extra="forbid"))
class Proxy:
    allowed_endpoints: ComplexList[NetworkEndpoint] | None = field(default_factory=list)


@dataclass(config=dict(extra="forbid"))
class Job:
    console_patterns: ConsoleState
    deployment: Deployment
    target: Target

    version: PositiveInt = 1
    deadline: datetime = datetime.max
    timeouts: Timeouts = field(default_factory=Timeouts)

    proxy: Proxy | None = field(default_factory=Proxy)

    # Function called once all the objects have been converted from dict
    # to their dataclass equivalent and field validation succeeded
    def __post_init__(self):
        # Associate all the timeouts to their respective watchdogs
        for name, wd in self.console_patterns.watchdogs.items():
            wd.set_timeout(self.timeouts.watchdogs.get(name))

    # NOTE: For backwards compatibility
    @property
    def deployment_start(self):
        return self.deployment.start if self.deployment else None

    # NOTE: For backwards compatibility
    @property
    def deployment_continue(self):
        return self.deployment.continue_ if self.deployment else None

    @classmethod
    def common_template_resources(cls):
        return {
            **imagestore_template_resources(),
            **registry_template_resources(),
            **{k.lower(): v for k, v in config.job_environment_vars().items()}
        }

    @classmethod
    def render_template_with_resources(cls, job_str, machine=None, bucket=None, **kwargs) -> str:
        jinja_prefix = '#!jinja2\n'
        # TODO: When bumping the job desc version, uncomment the two lines below.
        # if not job_str.startswith(jinja_prefix):
        #     return job_str
        job_str = job_str.removeprefix(jinja_prefix)

        # TODO: deprecate all the fixed attributes
        template_params = {
            "ready_for_service": machine.ready_for_service if machine else True,
            "machine_id": machine.id if machine else "machine_id",
            "machine": machine.safe_attributes if machine else {},
            "machine_tags": machine.tags if machine else [],
            "local_tty_device": machine.local_tty_device if machine else "",
            **cls.common_template_resources(),
            **kwargs,
        }

        # TODO: deprecate all the fixed attributes
        if bucket:
            dut_creds = bucket.credentials('dut')

            template_params["minio_url"] = bucket.minio.url
            template_params["job_bucket"] = bucket.name
            template_params["job_bucket_access_key"] = dut_creds.username
            template_params["job_bucket_secret_key"] = dut_creds.password

        # Make sure the job never modifies any of the template parameters
        template_params = deepcopy(template_params)

        return Template(job_str, undefined=ChainableUndefined).render(**template_params)

    @classmethod
    def render_with_resources(cls, job_str, machine=None, bucket=None, render_job_template=True, **kwargs):
        try:
            if render_job_template:
                job_str = cls.render_template_with_resources(job_str, machine=machine, bucket=bucket, **kwargs)

            job = cls(**yaml.safe_load(job_str))

            # Make sure the default firmware boot time is set to the value that was learnt, if one was already learnt
            if job.timeouts.firmware_boot == Timeout() and machine is not None:
                if firmware_boot_time := machine.firmware_boot_time:
                    # Set the default firmware boot timeout 150% above the maximum boot time we saw, and a minimum of 5
                    # seconds in case power takes longer to set or something
                    job.timeouts.firmware_boot = Timeout(seconds=max(5, firmware_boot_time * 2.5), retries=3)
                    job.timeouts.firmware_boot.name = "firmware_boot"

            return job
        except Exception:
            backtrace = traceback.format_exc(limit=-1)

        raise ValueError(backtrace)

    @classmethod
    def from_path(cls, job_template_path, machine=None, bucket=None):
        with open(job_template_path, "r") as f_template:
            template_str = f_template.read()
            return Job.render_with_resources(template_str, machine, bucket)
