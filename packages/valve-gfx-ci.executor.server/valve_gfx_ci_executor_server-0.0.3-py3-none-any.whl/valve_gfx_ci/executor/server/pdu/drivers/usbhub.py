from collections.abc import Generator
from dataclasses import asdict
from enum import StrEnum, auto
from functools import cached_property
from pathlib import Path
import re

from pydantic import NonNegativeInt, DirectoryPath, field_validator, model_validator
from pydantic.dataclasses import dataclass

from .. import PDU, PDUPort, PDUPortState


USB_DEVICES_PATH = "/sys/bus/usb/devices"


class USBHubDevice:
    def __init__(self, base_path):
        self.base_path = Path(base_path).resolve()

        if self.bDeviceClass != 0x09:
            raise ValueError(f"The USB device at location '{self.base_path}' is not a USB hub")

        self.ports = [
            str(oid) for oid in [i + 1 for i in range(self.maxchild)] if self.port_path(oid).exists()
        ]

    def __hash__(self) -> int:
        return hash(self.base_path)

    def __eq__(self, o) -> bool:
        return self.base_path == o.base_path

    def __repr__(self) -> str:
        return (f"<USBHubDevice {self.busnum}-{self.devpath} - {self.idVendor:04x}:{self.idProduct:04x} ({self.speed} "
                f"Mbps) - {len(self.ports)} ports>")

    def __str__(self) -> str:
        return repr(self)

    def __read(self, filename) -> str:
        try:
            return (self.base_path / filename).read_text().strip()
        except Exception:
            return ""

    def __read_int(self, filename, base=10) -> int:
        if v := self.__read(filename):
            return int(v, base)

    @cached_property
    def busnum(self):
        return self.__read("busnum")

    @cached_property
    def devpath(self):
        return self.__read("devpath")

    @cached_property
    def serial(self):
        return self.__read("serial")

    @cached_property
    def maxchild(self):
        return self.__read_int("maxchild")

    @cached_property
    def idVendor(self):
        return self.__read_int("idVendor", 16)

    @cached_property
    def idProduct(self):
        return self.__read_int("idProduct", 16)

    @cached_property
    def bDeviceClass(self):
        return self.__read_int("bDeviceClass", 16)

    @cached_property
    def speed(self):
        return self.__read_int("speed")

    @cached_property
    def controller_path(self):
        path = self.base_path.parent
        while not path.name.startswith("usb") and path.name != "":
            path = path.parent
        return path.parent

    def port_path(self, port_id):
        paths = list(self.base_path.glob(f"*:1.0/*-port{port_id}/disable"))

        if len(paths) > 1:
            msg = f"Found more than one candidate port for port_id {port_id} in the hub at location '{self.base_path}'"
            raise ValueError(msg)
        elif len(paths) == 1:
            return paths[0]
        else:
            raise ValueError(f"No port id {port_id} in the hub at location '{self.base_path}'")

    def set_port_state(self, port_id, state):
        if state not in [PDUPortState.OFF, PDUPortState.ON]:
            raise ValueError(f"Unsupported state {state.name}")

        self.port_path(port_id).write_text("0\n" if state == PDUPortState.ON else "1\n")

    def get_port_state(self, port_id):
        state = self.port_path(port_id).read_text().strip()
        return PDUPortState.ON if state == "0" else PDUPortState.OFF

    def to_USBHubDeviceMatchConfig(self):
        return USBHubDeviceMatchConfig(devpath=self.devpath,
                                       idVendor=self.idVendor,
                                       idProduct=self.idProduct,
                                       maxchild=self.maxchild)

    @classmethod
    def list(cls) -> Generator['USBHubDevice']:  # pragma: nocover
        for devpath in Path(USB_DEVICES_PATH).iterdir():
            try:
                if hubdev := cls(devpath):
                    yield hubdev
            except Exception:
                pass


@dataclass
class USBHubDeviceMatchConfig:
    devpath: str
    idVendor: NonNegativeInt
    idProduct: NonNegativeInt

    maxchild: NonNegativeInt | None = None
    speed: NonNegativeInt | None = None

    @property
    def asdict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

    @field_validator("devpath")
    @classmethod
    def devpath_has_expected_format(cls, v):
        if not re.match(r"^(\d+\.?)*\d+$", v):
            raise ValueError("The devpath is not a dot-separated list of integers")
        return v

    def matches(self, hub):
        for field_name in self.asdict:
            if value := getattr(self, field_name):
                if getattr(hub, field_name) != value:
                    return False
        return True


class USBHubConfigUnknownStatePolicy(StrEnum):
    DO_NOTHING = auto()
    TURN_OFF = auto()
    TURN_ON = auto()
    RESTORE_LAST_STATE = auto()

    def wanted_state(self, last_state: PDUPortState) -> PDUPortState:
        if self == self.DO_NOTHING:
            return None
        elif self == self.TURN_OFF:
            return PDUPortState.OFF
        elif self == self.TURN_ON:
            return PDUPortState.ON
        elif self == self.RESTORE_LAST_STATE:
            if last_state and last_state != PDUPortState.UNKNOWN:
                return last_state
            else:
                return PDUPortState.OFF


@dataclass
class USBHubPDUConfig:
    controller: DirectoryPath | None = None
    devices: list[USBHubDeviceMatchConfig] | None = None

    serial: str | None = None

    on_unknown_port_state: USBHubConfigUnknownStatePolicy | None = USBHubConfigUnknownStatePolicy.RESTORE_LAST_STATE

    # Default paths
    USB_DEVICES_PATH = Path("/sys/bus/usb/devices")

    @field_validator("serial")
    @classmethod
    def serial_is_stripped(cls, v):
        return v.strip()

    @model_validator(mode="after")
    def ensure_we_have_the_right_parameters(self) -> "USBHubPDUConfig":
        if self.serial is not None:
            return self
        elif self.controller is not None and self.devices is not None:
            if len(self.devices) == 0:
                raise ValueError("At least one device should be set")
            return self
        else:
            raise ValueError("Neither a `serial` nor the tuple (`controller`, `devices`) was found in the config")

    @property
    def hubs(self):
        hubs = []
        if self.serial:
            for serial_path in self.USB_DEVICES_PATH.glob("*/serial"):
                if serial_path.read_text().strip() == self.serial:
                    try:
                        hubs.append(USBHubDevice(serial_path.parent))
                    except Exception:  # pragma: nocover
                        continue

            if len(hubs) == 0:
                raise ValueError(f"No USB Hubs with serial '{self.serial}' found")
        elif self.controller and self.devices:
            for dev_cfg in self.devices:
                dev_cfg_hubs = []
                for dev in self.controller.glob(f"usb*/**/*-{dev_cfg.devpath}"):
                    try:
                        hub = USBHubDevice(dev)
                    except Exception:
                        continue

                    if dev_cfg.matches(hub):
                        dev_cfg_hubs.append(hub)
                if len(dev_cfg_hubs) == 0:
                    raise ValueError(f"Could not find a USB device matching {dev_cfg}")
                elif len(dev_cfg_hubs) == 1:
                    hubs.extend(dev_cfg_hubs)
                else:
                    raise ValueError(f"Found more than one USB device match {dev_cfg}")

        return hubs


class USBHubPDU(PDU):
    driver_name = 'usbhub'

    @cached_property
    def usb_config(self):
        return USBHubPDUConfig(**self.config)

    @cached_property
    def associated_hubs(self):
        hubs = self.usb_config.hubs
        if len(hubs) == 0:
            return []

        # Use the first hub as a reference
        ref = hubs[0]

        # Ensure that all the hubs share the same controller (needed for serial-based devices)
        if not all([h.controller_path == ref.controller_path for h in hubs]):
            raise ValueError("Not all hubs are connected to the same USB controller")

        # Ensure that all the hubs have the same ports
        if not all([h.ports == ref.ports for h in hubs]):
            raise ValueError("Not all hubs agree on the list of ports")

        # Ensure that all the hubs have different speeds like they should if a controller had
        # support for multiple USB versions, but all connected to the same USB lines
        speeds = {h.speed for h in hubs}
        if len(speeds) != len(hubs):
            raise ValueError("Some hubs unexpectedly share the same speed")

        return hubs

    def __init__(self, name, config, reserved_port_ids=[]):
        super().__init__(name, config, reserved_port_ids)

        if len(list(self.associated_hubs)) == 0:
            raise ValueError("No associated hub devices found")

        self._ports = [
            PDUPort(self, str(oid))
            for oid in self.associated_hubs[0].ports
        ]

        self._last_state = PDUPortState.UNKNOWN

    @property
    def default_min_off_time(self):
        return 10.0

    @property
    def ports(self):
        return self._ports

    def set_port_state(self, port_id, state):
        for h in self.associated_hubs:
            h.set_port_state(port_id, state)

    def get_port_state(self, port_id):
        # Get the port's state
        states = {h.get_port_state(port_id) for h in self.associated_hubs}
        if len(states) == 1:
            state = states.pop()
        else:
            state = PDUPortState.UNKNOWN

            if wanted_state := self.usb_config.on_unknown_port_state.wanted_state(self._last_state):
                if not self.is_port_reserved(port_id):
                    self.set_port_state(port_id, wanted_state)
                    state = wanted_state

        # Store the state as the last one for future use
        self._last_state = state

        return state
