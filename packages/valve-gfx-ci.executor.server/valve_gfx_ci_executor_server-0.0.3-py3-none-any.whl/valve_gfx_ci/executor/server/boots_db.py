from dataclasses import field, fields

from jinja2 import Template, ChainableUndefined
from pydantic.dataclasses import dataclass
import usb.core
import yaml

from .android.fastbootd import FastbootDevice
from .job import DeploymentState, DhcpRequestMatcher, Job


@dataclass(kw_only=True)
class BootsDevice:
    defaults: DeploymentState


@dataclass
class USBMatcher:
    idVendor: int | list[int] | None = None
    idProduct: int | list[int] | None = None
    iManufacturer: str | list[str] | None = None
    iProduct: str | list[str] | None = None
    iSerialNumber: str | list[str] | None = None

    def matches(self, device: 'usb.core.Device'):
        for f in fields(self):
            if expected_values := getattr(self, f.name, None):
                if not isinstance(expected_values, list):
                    expected_values = [expected_values]

                if getattr(device, f.name) not in expected_values:
                    return False

        return True


@dataclass
class FastbootDeviceMatcher:
    # NOTE: All the specified values must be a match to be considered a valid match
    usb: USBMatcher | None = None
    variables: dict[str, str | list[str]] | None = field(default_factory=dict)  # The values are regular expressions

    def matches(self, fbdev: FastbootDevice) -> bool:
        if self.usb and not self.usb.matches(fbdev.device):
            return False

        # Match the expected variables
        fbdev_vars = fbdev.variables
        for name, expected_values in self.variables.items():
            if not isinstance(expected_values, list):
                expected_values = [expected_values]

            if fbdev_vars.get(name) not in expected_values:
                return False

        return True


@dataclass(kw_only=True)
class BootsDbFastbootDevice(BootsDevice):
    match: FastbootDeviceMatcher


@dataclass(kw_only=True)
class BootsDbDhcpDevice(BootsDevice):
    match: DhcpRequestMatcher


@dataclass
class BootsDB:
    fastboot: dict[str, BootsDbFastbootDevice] | None = field(default_factory=dict)
    dhcp: dict[str, BootsDbDhcpDevice] | None = field(default_factory=dict)

    @classmethod
    def render_with_resources(cls, db_str, job=None, **kwargs):
        jinja_prefix = '#!jinja2\n'
        if db_str.startswith(jinja_prefix):
            db_str = db_str.removeprefix(jinja_prefix)
            # TODO: When bumping the job desc version, move everything below into this `if`,
            # and in the `else` simply instantiate the class from the literal `db_str`.

        # Set here the minimum needed to get templates to work
        default_job = {
            "http": {
                "path_to": lambda *p: f"http://ci-gateway:12345/_/{"/".join(p)}",
            },
            "tftp": {
                "path_to": lambda *p: f"/_/{"/".join(p)}",
            }
        }

        template_params = {
            **Job.common_template_resources(),
            "job": job if job else default_job,
            **kwargs,
        }

        rendered_db_str = Template(db_str, undefined=ChainableUndefined).render(**template_params)
        return cls(**yaml.safe_load(rendered_db_str))

    @classmethod
    def from_path(cls, filepath, **kwargs):
        with open(filepath, "r") as f_template:
            db_str = f_template.read()
            return cls.render_with_resources(db_str, **kwargs)
