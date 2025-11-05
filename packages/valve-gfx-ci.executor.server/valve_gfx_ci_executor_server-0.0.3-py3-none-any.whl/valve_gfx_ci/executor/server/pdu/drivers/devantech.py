from .. import PDU, PDUPort, PDUPortState
from ..helpers import cache_with_expiration

import socket
from contextlib import contextmanager
from typing import Self


# in seconds
PORT_STATE_TIMEOUT = 0.2


class DevantechPDU(PDU):
    driver_name = 'devantech'

    def __init__(self, name, config, reserved_port_ids=[]):
        # When adding fields, make sure `__hash__` below is updated as needed
        self.host, self.port = config.get('hostname', 'localhost:17494').split(':')
        self.port = int(self.port)
        self.password = config.get('password', None)

        # mapping from module id -> number of relays
        self.devices = {18: 2,    # eth002
                        19: 8,    # eth008
                        20: 4,    # eth484
                        21: 20,   # eth8020
                        22: 4,    # wifi484
                        24: 20,   # wifi8020
                        26: 2,    # wifi002
                        28: 8,    # wifi008
                        51: 20,   # eth1620
                        52: 10}   # eth1610

        # Check for supported module
        with self.conn() as s:
            s.sendall(b"\x10")
            id = s.recv(3)[0]
            if id not in self.devices:
                raise ValueError("not supported module id found")

        self._ports = [PDUPort(self, i) for i in range(self.devices[id])]

        super().__init__(name, config, reserved_port_ids)

    @classmethod
    def network_probe(cls, ip_address: str, mac_address: str, dhcp_client_name: str = None) -> Self:
        return cls(f"{cls.driver_name}-{mac_address}", config={"hostname": f"{ip_address}:17494"})

    def __hash__(self):
        # Must include all fields necessary to distinguish from another instance
        return hash((self.host, self.port))

    @property
    def ports(self):
        return self._ports

    @contextmanager
    def conn(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))

            # Check to see if password is enabled
            s.sendall(b"\x7a")
            if s.recv(1)[0] == 0:
                passwordString = b'\x79' + self.password.encode()
                s.sendall(passwordString)
                if s.recv(1)[0] != 1:
                    raise ValueError("wrong password")

            yield s

    @cache_with_expiration(seconds=PORT_STATE_TIMEOUT)
    def _state(self):
        num_bytes = (len(self._ports) + 7) // 8

        with self.conn() as s:
            s.sendall(b'\x24')
            port_states = b''
            while len(port_states) != num_bytes:
                buf = s.recv(num_bytes - len(port_states), socket.MSG_WAITALL)
                if len(buf) == 0:
                    raise ValueError("we never received the expected amount of bytes")
                port_states += buf

            return port_states

    def set_port_state(self, port_id, state):
        msg = b'\x21' if state == PDUPortState.OFF else b'\x20'
        # NOTE: relays are 1-indexed in the SET command
        msg += int(port_id + 1).to_bytes(1, 'big')
        msg += b'\x00'

        with self.conn() as s:
            s.sendall(msg)
            if s.recv(1)[0] == 1:
                raise ValueError('failed to set port state')

        self._state.cache_clear()

    def get_port_state(self, port_id):
        byte_index = port_id // 8
        bit_position = port_id % 8

        if self._state()[byte_index] & (1 << bit_position):
            return PDUPortState.ON
        else:
            return PDUPortState.OFF
