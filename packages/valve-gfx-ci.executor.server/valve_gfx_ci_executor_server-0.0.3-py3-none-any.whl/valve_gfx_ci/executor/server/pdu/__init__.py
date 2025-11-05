from datetime import datetime
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Self

import time
from logging import getLogger, getLevelName, Formatter, StreamHandler


logger = getLogger(__name__)
logger.setLevel(getLevelName('INFO'))
log_formatter = \
    Formatter("%(asctime)s [%(threadName)s] [%(levelname)s] %(funcName)s: "
              "%(message)s")
logger.propagate = False
console_handler = StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)


class PDUPortState(IntEnum):
    UNKNOWN = 0
    OFF = 1
    ON = 2
    REBOOT = 3

    @classmethod
    def valid_actions(cls):
        return [s for s in PDUPortState if s.value > 0]

    @property
    def is_valid_action(self):
        return self in self.valid_actions()


@dataclass
class PDUPowerChannel:
    # Instant power usage of the channel, in Watts
    instant_power: float | None = None

    # Energy consumed since an arbitrary point in time, in Joules
    energy: float | None = None

    def __add__(self, other: Self):
        def add(a: float | None, b: float | None) -> float | None:
            if a is not None and b is not None:
                return a + b
            elif a is None:
                return b
            else:
                return a

        return type(self)(instant_power=add(self.instant_power, other.instant_power),
                          energy=add(self.energy, other.energy))

    def __mul__(self, other: float):
        def mul(a: float | None, b: float) -> float | None:
            if a is not None:
                return a * b
            else:
                return None

        return type(self)(instant_power=mul(self.instant_power, other),
                          energy=mul(self.energy, other))


@dataclass
class PDUPortFullState(PDUPowerChannel):
    state: PDUPortState = PDUPortState.UNKNOWN


class PDUPort:
    def __init__(self, pdu, port_id, label=None, min_off_time=5):
        self.pdu = pdu
        self.port_id = port_id
        self.label = label
        self.min_off_time = min_off_time

        self.last_polled = None
        self.last_known_full_state = PDUPortFullState()
        self.last_shutdown = None

    @property
    def last_known_state(self):
        return self.last_known_full_state.state

    @last_known_state.setter
    def last_known_state(self, value):
        self.last_known_full_state.state = value

    @property
    def reserved(self):
        return str(self.port_id) in self.pdu.reserved_port_ids

    @reserved.setter
    def reserved(self, value: bool):
        if value:
            self.pdu.reserve_port(self.port_id)
        else:
            self.pdu.unreserve_port(self.port_id)

    def set(self, state):
        if self.reserved:
            logger.error("Port is reserved")
            return

        # Check the current state before writing it
        cur_state = self.state
        logger.debug("set: %s -> %s", cur_state.name, state.name)
        if cur_state == state:
            return

        if cur_state == PDUPortState.OFF and state == PDUPortState.ON:
            # Enforce a minimum amount of time between state changes
            time_spent_off = (datetime.now() - self.last_shutdown).total_seconds()
            if time_spent_off < self.min_off_time:
                time.sleep(self.min_off_time - time_spent_off)

        self.pdu.set_port_state(self.port_id, state)

        # Update the port's properties
        if state == PDUPortState.OFF and self.last_known_state != PDUPortState.OFF:
            self.last_shutdown = datetime.now()
        self.last_known_state = state

    def _state_polled_event(self, state: PDUPortState):
        self.last_polled = datetime.now()

        # Reset the state
        if state == PDUPortState.OFF and (self.last_shutdown is None or self.last_known_state != PDUPortState.OFF):
            self.last_shutdown = self.last_polled

        self.last_known_state = state

        return state

    @property
    def state(self) -> PDUPortState:
        return self._state_polled_event(self.pdu.get_port_state(self.port_id))

    @property
    def full_state(self) -> PDUPortFullState:
        self.last_known_full_state = self.pdu.get_port_full_state(self.port_id)
        self._state_polled_event(self.last_known_full_state.state)
        return self.last_known_full_state

    def __eq__(self, other):
        for attr in ["pdu", "port_id", "label", "min_off_time"]:
            if getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True

    def __repr__(self):
        return (f"<PDU Port: PDU={self.pdu.name}, ID={self.port_id}, label={self.label}, "
                f"min_off_time={self.min_off_time}>")


@dataclass
class PDUPowerState:
    total_power: PDUPowerChannel = None
    power_channels: dict[str, PDUPowerChannel] = field(default_factory=dict)


class PDU:
    # NOTICE: Please pass the config parameter directly from the user,
    # without modifications.
    def __init__(self, name, config, reserved_port_ids=[]):
        self.name = name
        self.config = config
        self.reserved_port_ids = set([str(p) for p in reserved_port_ids])

        # FIXME: It would be better to poll on state changes than wait
        # arbitrary amounts of time. Abstracting state transitions
        # into a method, so that subclasses can do more intelligent
        # things (in SNMP, a better thing can be done, for instance),
        # would be a start. There's a couple things in play for these pauses,
        #  1. The firmware on different PDUs needs differing amounts
        #  of time to settle in state transitions.  2. SNMP PDUs
        #  typically offer a way for the user to add state transition
        #  delays of their own, and these come with defaults that we
        #  need to wait *at least* that long for. We should do a
        #  better job of provisioning these values to suit our needs.
        if not hasattr(self, 'state_transition_delay_seconds'):
            self.state_transition_delay_seconds = 1

    @property
    def ports(self):
        # NOTICE: Left for drivers to implement
        # WARNING: Try to keep the list of returned ports constant, but do
        #          update the port properties (label / reservation) on every
        #          call. This allows keeping port metadata such as
        #          `last_shutdown` accurate across multiple polls.
        return []

    def set_port_state(self, port_id, state):
        # NOTICE: Left for drivers to implement
        return False

    def get_port_state(self, port_id):
        # NOTICE: Left for drivers to implement
        return PDUPortState.UNKNOWN

    def get_port_full_state(self, port_id):
        # NOTICE: Left for drivers to implement
        return PDUPortFullState(state=self.get_port_state(port_id))

    @property
    def power_state(self) -> PDUPowerState:
        return PDUPowerState()

    def reserve_port(self, port_id):
        self.reserved_port_ids.add(str(port_id))

    def unreserve_port(self, port_id):
        try:
            self.reserved_port_ids.remove(str(port_id))
        except KeyError:
            pass

    def is_port_reserved(self, port_id) -> bool:
        return str(port_id) in self.reserved_port_ids

    @property
    def default_min_off_time(self):
        return 30

    def __eq__(self, other):
        return all([
            getattr(self, attr, None) == getattr(other, attr, None)
            for attr in ["name",
                         "config",
                         "reserved_port_ids"]])

    @classmethod
    def supported_pdus(cls):
        from .drivers.apc import ApcMasterswitchPDU
        from .drivers.cyberpower import PDU41004, PDU15SWHVIEC12ATNET
        from .drivers.dummy import DummyPDU
        from .drivers.virtual import VirtualPDU
        from .drivers.snmp import ManualSnmpPDU
        from .drivers.shelly import ShellyPDU
        from .drivers.tasmota import TasmotaPDU
        from .drivers.devantech import DevantechPDU
        from .drivers.kernelchip import KernelChipPDU
        from .drivers.usbhub import USBHubPDU
        from .drivers.snmp_poe import SnmpPoePDU, SnmpPoeTpLinkPDU

        drivers = [
            ApcMasterswitchPDU,
            PDU41004,
            PDU15SWHVIEC12ATNET,
            DummyPDU,
            VirtualPDU,
            ManualSnmpPDU,
            ShellyPDU,
            TasmotaPDU,
            DevantechPDU,
            KernelChipPDU,
            USBHubPDU,
            SnmpPoePDU,
            SnmpPoeTpLinkPDU
        ]

        return {d.driver_name: d for d in drivers}

    @classmethod
    def create(cls, model_name, pdu_name, config, reserved_port_ids=[]):
        driver = cls.supported_pdus().get(model_name)

        if driver is None:
            raise ValueError(f"Unknown model name '{model_name}'")

        return driver(pdu_name, config, reserved_port_ids)


class PDUSimpleNetworkProbeMixin:
    @classmethod
    def network_probe(cls, ip_address: str, mac_address: str, dhcp_client_name: str = None) -> Self:
        return cls(f"{cls.driver_name}-{mac_address}", config={"hostname": ip_address})
