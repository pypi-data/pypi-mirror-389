from unittest.mock import MagicMock, patch, PropertyMock
import pytest
import time

from server.pdu import PDUPortState
from server.pdu.drivers.snmp import (
    retry_on_known_errors,
    SnmpPDU,
    Session
)


def _reset_easysnmp_mock(monkeypatch):
    import server.pdu.drivers.snmp as snmp

    session_mock = MagicMock()
    sleep_mock = MagicMock()

    ports = []
    for port_id in range(16):
        ports.append(MagicMock(oid=f"mib-2.105.1.1.1.3.1.{port_id + 1}", value=f"Port {port_id + 1}"))
    session_mock.return_value.walk.return_value = ports

    # REVIEW: I wonder if there's a clever way of covering the
    # difference in import locations between here and snmp.py
    monkeypatch.setattr(snmp, "Session", session_mock)
    monkeypatch.setattr(time, "sleep", sleep_mock)

    return session_mock, sleep_mock


@pytest.fixture(autouse=True)
def reset_easysnmp_mock(monkeypatch):
    global Session, time_sleep
    Session, time_sleep = _reset_easysnmp_mock(monkeypatch)


@patch("random.random", return_value=0.42)
def test_driver_BaseSnmpPDU_retry_on_known_errors__known_error(random_mock):
    global retriable_error_call_count
    retriable_error_call_count = 0

    @retry_on_known_errors
    def retriable_error():
        global retriable_error_call_count

        assert time_sleep.call_count == retriable_error_call_count

        retriable_error_call_count += 1
        raise SystemError("<built-in function set> returned NULL without setting an error")

    with pytest.raises(ValueError):
        retriable_error()

    time_sleep.assert_called_with(1.42)
    assert time_sleep.call_count == retriable_error_call_count
    assert retriable_error_call_count == 3


class MockSnmpPDU(SnmpPDU):
    outlet_labels = '1.3.6.1.4.1.1234.1.2.3.4.4.5.4.5'
    outlet_status = '1.3.6.1.4.1.1234.1.2.3.4.4.5.4.6'
    outlet_power = '1.3.6.1.4.1.1234.1.2.3.4.4.5.4.7'
    outlet_power_multiplier = 2.0

    state_mapping = {
        PDUPortState.ON: 2,
        PDUPortState.OFF: 3,
        PDUPortState.REBOOT: 4,
    }

    state_transition_delay_seconds = 5


def test_driver_SnmpPDU_eq():
    params = {
        "hostname": "hostname",
        "community": "community"
    }

    assert MockSnmpPDU("name", params) == MockSnmpPDU("name", params)
    for param in params:
        n_params = dict(params)
        n_params[param] = "modified"
        assert MockSnmpPDU("name", params) != MockSnmpPDU("name", n_params)


def test_driver_SnmpPDU_listing_ports():
    walk_mock = Session.return_value.walk
    walk_mock.return_value = [MagicMock(value="P1"), MagicMock(value="P2")]

    pdu = MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})
    walk_mock.assert_called_with(pdu.outlet_labels_oid)
    ports = pdu.ports

    # Check that the labels are stored, and the port IDs are 1-indexed
    for i in range(0, 2):
        assert ports[i].port_id == i+1
        assert ports[i].label == f"P{i+1}"


def test_driver_SnmpPDU_listing_ports__walk_failure():
    err_msg = "<built-in function walk> returned NULL without setting an error"
    Session.return_value.walk.side_effect = SystemError(err_msg)

    with pytest.raises(ValueError):
        MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})


def test_driver_BaseSnmpPDU_port_label_mapping():
    walk_mock = Session.return_value.walk
    set_mock = Session.return_value.set
    walk_mock.return_value = [
        MagicMock(oid="1.2.3.4.5.10", value="P1"),
        MagicMock(oid="1.2.3.4.5.13", value="P2")
    ]

    pdu = MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})

    # Make sure that the OIDs generated follow the index we got in the walk
    assert pdu.outlet_ctrl_oid(1) == "1.3.6.1.4.1.1234.1.2.3.4.4.5.4.6.10"
    assert pdu.outlet_ctrl_oid(2) == "1.3.6.1.4.1.1234.1.2.3.4.4.5.4.6.13"

    set_mock.return_value = True
    assert pdu.set_port_state("P1", PDUPortState.REBOOT) is True
    set_mock.assert_called_with(pdu.outlet_ctrl_oid(1), pdu.state_mapping[PDUPortState.REBOOT], 'i')
    assert pdu.set_port_state("P2", PDUPortState.REBOOT) is True
    set_mock.assert_called_with(pdu.outlet_ctrl_oid(2), pdu.state_mapping[PDUPortState.REBOOT], 'i')
    with pytest.raises(ValueError):
        pdu.set_port_state("flubberbubber", PDUPortState.OFF)


def test_driver_BaseSnmpPDU_get_port():
    get_mock = Session.return_value.get

    pdu = MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})
    get_mock.return_value.value = pdu.state_mapping[PDUPortState.REBOOT]
    pdu_state = pdu.get_port_state(2)
    assert pdu_state == PDUPortState.REBOOT
    get_mock.assert_called_with(pdu.outlet_status_oid(2))

    get_mock.side_effect = SystemError("<built-in function get> returned NULL without setting an error")
    with pytest.raises(ValueError):
        pdu.get_port_state(2)


def test_driver_BaseSnmpPDU_get_port_full_state():
    get_mock = Session.return_value.get

    pdu = MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})

    # Check that the outlet_power_oid() function returns the expected OID
    assert pdu.outlet_power_oid(1) == "1.3.6.1.4.1.1234.1.2.3.4.4.5.4.7.1"

    get_mock.side_effect = [MagicMock(value=pdu.state_mapping[PDUPortState.REBOOT]),
                            MagicMock(value=42)]
    port_state = pdu.get_port_full_state(2)

    assert port_state.state == PDUPortState.REBOOT
    get_mock.assert_any_call(pdu.outlet_status_oid(2))

    assert port_state.instant_power == 84
    get_mock.assert_any_call(pdu.outlet_power_oid(2))


def test_driver_BaseSnmpPDU_set_port():
    set_mock = Session.return_value.set

    pdu = MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})
    type(set_mock).value = PropertyMock(return_value=pdu.state_mapping[PDUPortState.REBOOT])
    set_mock.return_value = True
    set_mock.assert_not_called()
    assert pdu.set_port_state(2, PDUPortState.REBOOT) is True
    set_mock.assert_called_with(pdu.outlet_ctrl_oid(2), pdu.state_mapping[PDUPortState.REBOOT], 'i')

    set_mock.side_effect = SystemError("<built-in function set> returned NULL without setting an error")
    with pytest.raises(ValueError):
        pdu.set_port_state(2, PDUPortState.REBOOT)


def test_driver_BaseSnmpPDU_action_translation():
    pdu = MockSnmpPDU("MyPDU", {"hostname": "127.0.0.1"})

    # Check the state -> SNMP value translation
    for action in PDUPortState.valid_actions():
        assert pdu.inverse_state_mapping[pdu.state_mapping[action]] == action

    with pytest.raises(KeyError):
        pdu.state_mapping[PDUPortState.UNKNOWN]
