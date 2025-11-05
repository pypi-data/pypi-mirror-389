import pytest

from server.pdu.drivers.cyberpower import PDU41004
from server.tests.test_pdu_basesnmp import _reset_easysnmp_mock


@pytest.fixture(autouse=True)
def reset_easysnmp_mock(monkeypatch):
    global Session, time_sleep
    Session, time_sleep = _reset_easysnmp_mock(monkeypatch)


def test_driver_PDU41004_check_OIDs():
    pdu = PDU41004("MyPDU", {"hostname": "127.0.0.1"})
    assert pdu.outlet_labels_oid == "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.2"
    assert pdu.outlet_status_oid(10) == "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4.10"
    assert pdu.outlet_ctrl_oid(10) == "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4.10"
