from unittest.mock import patch
import pytest

from server.pdu import PDUPortState
from server.pdu.drivers.kernelchip import KernelChipPDU


class KernelChipBaseMock:
    def __init__(self, *args, **kwargs):
        self.password = kwargs.get('password', None)
        self.states = b'1111111011101101110010101111'
        self._data_to_recv = b'#FLG,AB,11,11\r\nJConfig from FLASH\r\n'
        self.auth = self.password is None

    def setsockopt(self, level, optname, value):
        pass

    def connect(self, address):
        pass  # Simulate a successful connection

    def recv(self, bufsize, flags=0):
        (ret, self._data_to_recv) = (self._data_to_recv[0:2], self._data_to_recv[2:])
        return ret

    def sendall(self, data):
        if not data.endswith(b'\r\n'):  # pragma: no cover
            self._data_to_recv += b'#ERR\r\n'
            return

        (ke, *msg) = data[:-2].split(b',')
        if ke != b'$KE':  # pragma: no cover
            self._data_to_recv += b'#ERR\r\n'
        elif msg == []:
            self._data_to_recv += b'#OK\r\n'
        elif msg == [b'INF']:  # pragma: no cover
            self._data_to_recv += b'#INF,Laurent-XXX,XXXX,XXXX-XXXX-XXXX-XXXX\r\n'
        elif len(msg) == 3 and msg[0] == b'PSW' and msg[1] == b'SET':
            if self.password == msg[2]:
                self._data_to_recv += b'#PSW,SET,OK\r\n'
                self.auth = True
            else:
                self._data_to_recv += b'#PSW,SET,ERR\r\n'
        elif msg[0] == b'REL':
            # no cover, because the driver verifies password earlier
            if not self.auth:  # pragma: no cover
                self._data_to_recv += b'#Access denied. Password is needed.\r\n'
                return

            port = int(str(msg[1], 'ascii'))
            if port < 1 or port > len(self.states):  # pragma: no cover
                self._data_to_recv += b'#REL,ERR\r\n'
            else:
                self.states = self.states[:port - 1] + msg[2][:] + self.states[port:]
                self._data_to_recv += b'#REL,OK\r\n'
        elif msg[0] == b'RDR' and len(msg) == 2:
            if not self.auth:
                self._data_to_recv += b'#Access denied. Password is needed.\r\n'
                return

            if msg[1] == b'ALL':
                self._data_to_recv += b'#RDR,ALL,' + self.states + b'\r\n'
            else:  # pragma: no cover
                port = int(str(msg[1], 'ascii'))
                if port < 1 or port > len(self.states):
                    self._data_to_recv += b'#RDR,ERR\r\n'
                elif self.states[port - 1] == ord(b'1'):
                    self._data_to_recv += b'#RDR,' + msg[1] + b',1\r\n'
                else:
                    self._data_to_recv += b'#RDR,' + msg[1] + b',0\r\n'
        else:  # pragma: no cover
            self._data_to_recv += b'#ERR\r\n'

    def close(self):
        pass

    # Context manager protocol methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@patch('socket.socket', new=KernelChipBaseMock)
def test_kernelchip_no_password_successful_connection():
    pdu = KernelChipPDU("TestPDU", {})

    assert len(pdu.ports) == 28
    assert pdu.get_port_state(1) == PDUPortState.ON
    assert pdu.get_port_state(2) == PDUPortState.ON
    assert pdu.get_port_state(3) == PDUPortState.ON
    assert pdu.get_port_state(4) == PDUPortState.ON
    assert pdu.get_port_state(5) == PDUPortState.ON
    assert pdu.get_port_state(6) == PDUPortState.ON
    assert pdu.get_port_state(7) == PDUPortState.ON
    assert pdu.get_port_state(8) == PDUPortState.OFF
    assert pdu.get_port_state(9) == PDUPortState.ON
    assert pdu.get_port_state(10) == PDUPortState.ON
    assert pdu.get_port_state(11) == PDUPortState.ON
    assert pdu.get_port_state(12) == PDUPortState.OFF
    assert pdu.get_port_state(13) == PDUPortState.ON
    assert pdu.get_port_state(14) == PDUPortState.ON
    assert pdu.get_port_state(15) == PDUPortState.OFF
    assert pdu.get_port_state(16) == PDUPortState.ON
    assert pdu.get_port_state(17) == PDUPortState.ON
    assert pdu.get_port_state(18) == PDUPortState.ON
    assert pdu.get_port_state(19) == PDUPortState.OFF
    assert pdu.get_port_state(20) == PDUPortState.OFF
    assert pdu.get_port_state(21) == PDUPortState.ON
    assert pdu.get_port_state(22) == PDUPortState.OFF
    assert pdu.get_port_state(23) == PDUPortState.ON
    assert pdu.get_port_state(24) == PDUPortState.OFF
    assert pdu.get_port_state(25) == PDUPortState.ON
    assert pdu.get_port_state(26) == PDUPortState.ON
    assert pdu.get_port_state(27) == PDUPortState.ON
    assert pdu.get_port_state(28) == PDUPortState.ON


@patch('socket.socket', new=KernelChipBaseMock)
def test_kernelchip_get_port_state__invalid_port_id():
    pdu = KernelChipPDU("TestPDU", {})

    assert len(pdu.ports) == 28
    with pytest.raises(ValueError) as excinfo:
        pdu.get_port_state(29)

    assert str(excinfo.value) == "Invalid port id"


@patch('socket.socket', new=KernelChipBaseMock)
def test_kernelchip_set_port_state():
    pdu = KernelChipPDU("TestPDU", {})

    assert len(pdu.ports) == 28
    pdu.set_port_state(1, PDUPortState.OFF)


@patch('socket.socket', new=KernelChipBaseMock)
def test_kernelchip_set_port_state__bad_invalid_port_id():
    pdu = KernelChipPDU("TestPDU", {})

    assert len(pdu.ports) == 28
    with pytest.raises(ValueError) as excinfo:
        pdu.set_port_state(29, PDUPortState.OFF)

    assert str(excinfo.value) == "Invalid port id"


@patch('socket.socket', new=KernelChipBaseMock)
def test_kernelchip_port_state_management():
    import time
    pdu = KernelChipPDU("TestPDU", {})

    assert pdu.get_port_state(1) == PDUPortState.ON
    time.sleep(0.5)
    assert pdu.get_port_state(1) == PDUPortState.ON


class KernelChipPasswordMock(KernelChipBaseMock):
    def __init__(self, *args, **kwargs):
        super().__init__(self, args, password=b'PassWord')


@patch('socket.socket', new=KernelChipPasswordMock)
def test_kernelchip_correct_password():
    pdu = KernelChipPDU("TestPDU", {'password': 'PassWord'})

    assert len(pdu.ports) == 28
    assert pdu.get_port_state(1) == PDUPortState.ON


@patch('socket.socket', new=KernelChipPasswordMock)
def test_kernelchip_incorrect_password():
    with pytest.raises(ValueError) as excinfo:
        KernelChipPDU("TestPDU", {'password': 'NoPassWord'})

    assert str(excinfo.value) == "Password Verification failure"


@patch('socket.socket', new=KernelChipPasswordMock)
def test_kernelchip_no_password():
    with pytest.raises(ValueError) as excinfo:
        KernelChipPDU("TestPDU", {})

    assert str(excinfo.value) == "Password is required"


class KernelChipInvalidFirstByteMock(KernelChipBaseMock):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self._data_to_recv = b'abc\r\n'


@patch('socket.socket', new=KernelChipInvalidFirstByteMock)
def test_kernelchip_parse_error__invalid_first_byte():
    with pytest.raises(ValueError) as excinfo:
        KernelChipPDU("TestPDU", {})

    assert str(excinfo.value) == "Invalid first byte"


class KernelChipDuplicateCRMock(KernelChipBaseMock):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self._data_to_recv = b'abc\r\r\n'


@patch('socket.socket', new=KernelChipDuplicateCRMock)
def test_kernelchip_parse_error__duplicate_cr():
    with pytest.raises(ValueError) as excinfo:
        KernelChipPDU("TestPDU", {})

    assert str(excinfo.value) == "Duplicate '\\r'"


class KernelChipRespondErrMock(KernelChipBaseMock):
    def sendall(self, data):
        self._data_to_recv += b'#ERR\r\n'


@patch('socket.socket', new=KernelChipRespondErrMock)
def test_kernelchip_parse_error__respond_err():
    with pytest.raises(ValueError) as excinfo:
        KernelChipPDU("TestPDU", {})

    assert str(excinfo.value) == "Protocol error"


class KernelChipIncorrectRdrAllResponseMock(KernelChipBaseMock):
    def sendall(self, data):
        if data == b'$KE,RDR,ALL\r\n':
            self._data_to_recv += b'#RDR,ABC,123\r\n'
        else:
            super().sendall(data)


@patch('socket.socket', new=KernelChipIncorrectRdrAllResponseMock)
def test_kernelchip_parse_error__incorrect_rdr_all_response():
    with pytest.raises(ValueError) as excinfo:
        KernelChipPDU("TestPDU", {})

    assert str(excinfo.value) == "Failure getting relays state"


class KernelChipIncorrectRelResponseMock(KernelChipBaseMock):
    def sendall(self, data):
        if data.startswith(b'$KE,REL,'):
            self._data_to_recv += b'#REL,ABC\r\n'
        else:
            super().sendall(data)


@patch('socket.socket', new=KernelChipIncorrectRelResponseMock)
def test_kernelchip_parse_error__incorrect_rel_response():
    pdu = KernelChipPDU("TestPDU", {})

    with pytest.raises(ValueError) as excinfo:
        pdu.set_port_state(1, PDUPortState.OFF)

    assert str(excinfo.value) == "Incorrect response"


@patch("server.pdu.drivers.kernelchip.KernelChipPDU.__new__")
def test_devantech_network_probe(init_mock):
    KernelChipPDU.network_probe(ip_address="10.42.0.1", mac_address="00:01:02:03:04:05")
    init_mock.assert_called_once_with(KernelChipPDU, "kernelchip-00:01:02:03:04:05",
                                      config={"hostname": "10.42.0.1:2424"})
