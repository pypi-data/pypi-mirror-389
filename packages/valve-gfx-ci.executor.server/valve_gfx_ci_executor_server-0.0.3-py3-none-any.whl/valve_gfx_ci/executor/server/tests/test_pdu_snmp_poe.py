from unittest.mock import MagicMock
import pytest

from server.pdu.drivers.snmp_poe import SnmpPoePDU, SnmpPoeTpLinkPDU
from server.tests.test_pdu_basesnmp import _reset_easysnmp_mock


@pytest.fixture(autouse=True)
def reset_easysnmp_mock(monkeypatch):
    global Session, time_sleep
    Session, time_sleep = _reset_easysnmp_mock(monkeypatch)


def test_driver_SnmpPoePDU_default_min_off_time():
    assert SnmpPoePDU("MyPDU", config={"hostname": "127.0.0.1"}).default_min_off_time == 10.0


def test_driver_SnmpPoeTpLinkPDU_default_min_off_time():
    assert SnmpPoeTpLinkPDU("MyPDU", config={"hostname": "127.0.0.1"}).default_min_off_time == 10.0


def test_driver_SnmpPoeTpLinkPDU_power_state():
    power_in_watts = 123

    get_mock = Session.return_value.get

    pdu = SnmpPoePDU("MyPDU", config={"hostname": "127.0.0.1"})

    # Pre-load the phase count and check the reporting
    get_mock.return_value = MagicMock(value=str(power_in_watts))
    assert pdu.power_state.total_power.instant_power == power_in_watts
    get_mock.assert_called_with('1.3.6.1.2.1.105.1.3.1.1.4.1')
