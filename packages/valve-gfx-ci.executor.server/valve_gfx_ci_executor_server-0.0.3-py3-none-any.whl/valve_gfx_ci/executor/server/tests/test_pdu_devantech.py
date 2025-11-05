from unittest.mock import patch
import pytest

from server.pdu import PDUPortState
from server.pdu.drivers.devantech import DevantechPDU


class DevantechEth0020SocketNoPasswordMock:
    def __init__(self, *args, **kwargs):
        self._data_to_recv = None

    def connect(self, address):
        pass  # Simulate a successful connection

    def recv(self, bufsize, flags=0):
        assert (len(self._data_to_recv) == bufsize)
        return self._data_to_recv

    def sendall(self, data):
        if data == b'\x10':
            self._data_to_recv = b'\x15\x00\x00'
        elif data[0] == 0x20:
            assert data == b'\x20\x01\x00'
            self._data_to_recv = b'\x00'
        elif data == b'\x24':
            self._data_to_recv = b'\x60\x80\x0c'
        elif data == b'\x7a':
            self._data_to_recv = b'\xff'
        pass

    def close(self):
        pass

    # Context manager protocol methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@patch('socket.socket', new=DevantechEth0020SocketNoPasswordMock)
def test_devantech_eth0020_no_password_successful_connection():
    pdu = DevantechPDU("TestPDU", {})

    assert len(pdu.ports) == 20
    assert pdu.get_port_state(0) == PDUPortState.OFF
    assert pdu.get_port_state(1) == PDUPortState.OFF
    assert pdu.get_port_state(2) == PDUPortState.OFF
    assert pdu.get_port_state(3) == PDUPortState.OFF
    assert pdu.get_port_state(4) == PDUPortState.OFF
    assert pdu.get_port_state(5) == PDUPortState.ON
    assert pdu.get_port_state(6) == PDUPortState.ON
    assert pdu.get_port_state(7) == PDUPortState.OFF
    assert pdu.get_port_state(8) == PDUPortState.OFF
    assert pdu.get_port_state(9) == PDUPortState.OFF
    assert pdu.get_port_state(10) == PDUPortState.OFF
    assert pdu.get_port_state(11) == PDUPortState.OFF
    assert pdu.get_port_state(12) == PDUPortState.OFF
    assert pdu.get_port_state(13) == PDUPortState.OFF
    assert pdu.get_port_state(14) == PDUPortState.OFF
    assert pdu.get_port_state(15) == PDUPortState.ON
    assert pdu.get_port_state(16) == PDUPortState.OFF
    assert pdu.get_port_state(17) == PDUPortState.OFF
    assert pdu.get_port_state(18) == PDUPortState.ON
    assert pdu.get_port_state(19) == PDUPortState.ON

    pdu.set_port_state(0, PDUPortState.ON)


class DevantechEth008SocketPasswordMock:
    def __init__(self, *args, **kwargs):
        self._data_to_recv = None

    def connect(self, address):
        pass  # Simulate a successful connection

    def recv(self, bufsize, flags=0):
        assert (len(self._data_to_recv) == bufsize)
        return self._data_to_recv

    def sendall(self, data):
        if data == b'\x10':
            self._data_to_recv = b'\x13\x00\x00'
        elif data == b'\x24':
            self._data_to_recv = b'\x98'
        elif data == b'\x7a':
            self._data_to_recv = b'\x00'
        elif data.startswith(b'\x79'):
            # Verify password
            if data[1:] == b'top-secret':
                self._data_to_recv = b'\x01'
            else:
                self._data_to_recv = b'\x02'
        pass

    def close(self):
        pass

    # Context manager protocol methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@patch('socket.socket', new=DevantechEth008SocketPasswordMock)
def test_devantech_eth008_password_successful_connection():
    pdu = DevantechPDU("TestPDU", {"password": "top-secret"})

    assert len(pdu.ports) == 8
    assert pdu.get_port_state(0) == PDUPortState.OFF
    assert pdu.get_port_state(1) == PDUPortState.OFF
    assert pdu.get_port_state(2) == PDUPortState.OFF
    assert pdu.get_port_state(3) == PDUPortState.ON
    assert pdu.get_port_state(4) == PDUPortState.ON
    assert pdu.get_port_state(5) == PDUPortState.OFF
    assert pdu.get_port_state(6) == PDUPortState.OFF
    assert pdu.get_port_state(7) == PDUPortState.ON


@patch('socket.socket', new=DevantechEth008SocketPasswordMock)
def test_devantech_eth008_wrong_password():
    with pytest.raises(ValueError) as excinfo:
        DevantechPDU("TestPDU", {"password": "not-top-secret"})

    assert str(excinfo.value) == "wrong password"


class DevantechUnknownIdSocketMock:
    def __init__(self, *args, **kwargs):
        self._data_to_recv = None

    def connect(self, address):
        pass  # Simulate a successful connection

    def recv(self, bufsize, flags=0):
        assert (len(self._data_to_recv) == bufsize)
        return self._data_to_recv

    def sendall(self, data):
        if data == b'\x10':
            self._data_to_recv = b'\x42\x00\x00'
        elif data == b'\x7a':
            self._data_to_recv = b'\xff'
        pass

    def close(self):
        pass

    # Context manager protocol methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@patch('socket.socket', new=DevantechUnknownIdSocketMock)
def test_devantech_unknown_id():
    with pytest.raises(ValueError) as excinfo:
        DevantechPDU("TestPDU", {})

    assert str(excinfo.value) == "not supported module id found"


class DevantechSetPortStateFailSocketMock:
    def __init__(self, *args, **kwargs):
        self._data_to_recv = None

    def connect(self, address):
        pass  # Simulate a successful connection

    def recv(self, bufsize, flags=0):
        assert (len(self._data_to_recv) == bufsize)
        return self._data_to_recv

    def sendall(self, data):
        if data == b'\x10':
            self._data_to_recv = b'\x13\x00\x00'
        elif data.startswith(b'\x20'):
            self._data_to_recv = b'\x01'  # failed to set port state
        elif data == b'\x7a':
            self._data_to_recv = b'\xff'
        pass

    def close(self):
        pass

    # Context manager protocol methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@patch('socket.socket', new=DevantechSetPortStateFailSocketMock)
def test_devantech_set_port_state_fail():
    pdu = DevantechPDU("TestPDU", {})

    with pytest.raises(ValueError) as excinfo:
        pdu.set_port_state(0, PDUPortState.ON)

    assert str(excinfo.value) == "failed to set port state"


class DevantechGetPortStateFailSocketMock:
    def __init__(self, *args, **kwargs):
        self._data_to_recv = None

    def connect(self, address):
        pass  # Simulate a successful connection

    def recv(self, bufsize, flags=0):
        return self._data_to_recv

    def sendall(self, data):
        if data == b'\x10':
            self._data_to_recv = b'\x13\x00\x00'
        elif data.startswith(b'\x24'):
            self._data_to_recv = b''  # failed to get port state
        elif data == b'\x7a':
            self._data_to_recv = b'\xff'
        pass

    def close(self):
        pass

    # Context manager protocol methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@patch('socket.socket', new=DevantechGetPortStateFailSocketMock)
def test_devantech_get_port_state_fail():
    pdu = DevantechPDU("TestPDU", {})

    with pytest.raises(ValueError) as excinfo:
        pdu.get_port_state(0)

    assert str(excinfo.value) == "we never received the expected amount of bytes"


@patch("server.pdu.drivers.devantech.DevantechPDU.__new__")
def test_devantech_network_probe(init_mock):
    DevantechPDU.network_probe(ip_address="10.42.0.1", mac_address="00:01:02:03:04:05")
    init_mock.assert_called_once_with(DevantechPDU, "devantech-00:01:02:03:04:05",
                                      config={"hostname": "10.42.0.1:17494"})
