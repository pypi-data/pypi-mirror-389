from .. import logger, PDU, PDUPort, PDUPortState

import socket
from contextlib import contextmanager


class VirtualPDU(PDU):  # pragma: nocover
    driver_name = 'vpdu'

    def __init__(self, name, config, reserved_port_ids=[]):
        logger.debug("Creating a virtual PDU named %s", name)
        self.host, self.port = config.get('hostname', 'localhost:9191').split(':')
        self.port = int(self.port)
        logger.debug("Connecting to %s:%d", self.host, self.port)
        with self.conn() as s:
            s.sendall((0).to_bytes(4, byteorder='big'))
            num_ports = int(s.recv(1)[0])
            self._ports = [PDUPort(self, i) for i in range(num_ports)]
        super().__init__(name, config, reserved_port_ids)

    @property
    def default_min_off_time(self):
        return 0.1

    @property
    def ports(self):
        return self._ports

    @contextmanager
    def conn(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            s.connect((self.host, self.port))
            yield s

    def set_port_state(self, port_id, state):
        if state == PDUPortState.OFF or state == PDUPortState.REBOOT:
            cmd = (port_id << 2) | 0x02
            with self.conn() as s:
                s.sendall(cmd.to_bytes(4, byteorder='big'))
                assert (s.recv(1)[0] == 0x01)
        if state == PDUPortState.ON or state == PDUPortState.REBOOT:
            cmd = (port_id << 2) | 0x01
            with self.conn() as s:
                s.sendall(cmd.to_bytes(4, byteorder='big'))
                assert (s.recv(1)[0] == 0x01)

    def get_port_state(self, port_id):
        cmd = port_id << 2 | 0x03
        with self.conn() as s:
            s.sendall(cmd.to_bytes(4, byteorder='big'))
            state = int(s.recv(1)[0])
            logger.debug("port state %x", state)
            if state == 0x03:
                return PDUPortState.ON
            elif state == 0x04:
                return PDUPortState.OFF
            elif state == 0x05:
                return PDUPortState.UNKNOWN
            else:
                assert (False)
