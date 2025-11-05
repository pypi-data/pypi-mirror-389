from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest

from server.pdu import (
    PDUPortState,
    PDUPort,
    PDU,
    PDUSimpleNetworkProbeMixin,
    PDUPortFullState,
    PDUPowerChannel,
    PDUPowerState,
)


def test_PDUPortState_UNKNOW_is_invalid_action():
    assert PDUPortState.UNKNOWN not in PDUPortState.valid_actions()
    assert PDUPortState.UNKNOWN.is_valid_action is False


def test_PDUPortState_valid_actions_contain_basics():
    for action in ["ON", "OFF", "REBOOT"]:
        assert action in [s.name for s in PDUPortState.valid_actions()]
        assert getattr(PDUPortState, action).is_valid_action is True


def test_PDUPowerChannel__add():
    assert PDUPowerChannel() + PDUPowerChannel() == PDUPowerChannel()

    assert PDUPowerChannel(instant_power=1, energy=2) + PDUPowerChannel() == PDUPowerChannel(instant_power=1, energy=2)
    assert PDUPowerChannel() + PDUPowerChannel(instant_power=1, energy=2) == PDUPowerChannel(instant_power=1, energy=2)

    assert (PDUPowerChannel(instant_power=1, energy=2) + PDUPowerChannel(instant_power=2, energy=4) ==
            PDUPowerChannel(instant_power=3, energy=6))


def test_PDUPowerChannel__mul():
    assert PDUPowerChannel() * 1000 == PDUPowerChannel()
    assert PDUPowerChannel(instant_power=1, energy=2) * 3 == PDUPowerChannel(instant_power=3, energy=6)


def __pdu_port_mock():
    pdu = MagicMock(reserved_port_ids=[])
    pdu.name = "MyPDU"
    port = PDUPort(pdu, 42, label="My Port")

    return pdu, port


def test_PDUPort__defaults():
    pdu, port = __pdu_port_mock()

    assert port.label == "My Port"
    assert repr(port) == "<PDU Port: PDU=MyPDU, ID=42, label=My Port, min_off_time=5>"

    assert port.last_shutdown is None
    assert port.last_known_state == PDUPortState.UNKNOWN

    pdu.set_port_state.assert_not_called()
    pdu.get_port_state.assert_not_called()


def test_PDUPort__get_state_UNKNOWN_to_OFF():
    pdu, port = __pdu_port_mock()

    port.last_shutdown = None
    port.last_known_state = PDUPortState.UNKNOWN

    pdu.get_port_state.return_value = PDUPortState.OFF
    assert port.state == PDUPortState.OFF

    pdu.get_port_state.assert_called_with(42)
    assert datetime.now() - port.last_shutdown < timedelta(seconds=1)
    assert port.last_known_state == PDUPortState.OFF


def test_PDUPort__get_full_state_UNKNOWN_to_ON():
    pdu, port = __pdu_port_mock()

    port.last_shutdown = None
    port.last_known_state = PDUPortState.UNKNOWN

    pdu.get_port_full_state.return_value = PDUPortFullState(state=PDUPortState.ON)
    assert port.full_state.state == PDUPortState.ON

    assert port.last_shutdown is None
    assert port.last_known_state == PDUPortState.ON
    assert port.last_known_full_state == pdu.get_port_full_state.return_value


def test_PDUPort__get_state_ON_to_OFF():
    pdu, port = __pdu_port_mock()

    port.last_shutdown = None
    port.last_known_state = PDUPortState.ON

    pdu.get_port_state.return_value = PDUPortState.OFF
    assert port.state == PDUPortState.OFF

    assert port.last_shutdown is not None
    assert port.last_known_state == PDUPortState.OFF


def test_PDUPort__get_state_OFF_to_OFF():
    pdu, port = __pdu_port_mock()

    port.last_shutdown = wanted_last_shutdown = datetime.now()
    port.last_known_state = PDUPortState.OFF

    pdu.get_port_state.return_value = PDUPortState.OFF
    assert port.state == PDUPortState.OFF

    pdu.get_port_state.assert_called_with(42)
    assert port.last_shutdown == wanted_last_shutdown
    assert port.last_known_state == PDUPortState.OFF


@patch("time.sleep")
def test_PDUPort__setting_OFF_to_ON(sleep_mock):
    pdu, port = __pdu_port_mock()

    port.last_shutdown = wanted_last_shutdown = datetime.now()
    port.last_known_state = PDUPortState.OFF

    pdu.get_port_state.return_value = PDUPortState.OFF
    sleep_mock.assert_not_called()
    port.set(PDUPortState.ON)

    # Make sure the minimum off time was respected
    sleep_mock.assert_called_once()
    sleep_time = sleep_mock.call_args[0][0]
    assert (port.min_off_time - sleep_time) < 1.0

    pdu.set_port_state.assert_called_with(port.port_id, PDUPortState.ON)
    assert pdu.set_port_state.call_count == 1
    assert port.last_shutdown == wanted_last_shutdown
    assert port.last_known_state == PDUPortState.ON


@patch("time.sleep")
def test_PDUPort__setting_ON_to_OFF(sleep_mock):
    pdu, port = __pdu_port_mock()

    port.last_shutdown = None
    port.last_known_state = PDUPortState.ON

    pdu.get_port_state.return_value = PDUPortState.ON
    port.set(PDUPortState.OFF)

    sleep_mock.assert_not_called()
    pdu.set_port_state.assert_called_with(port.port_id, PDUPortState.OFF)
    assert pdu.set_port_state.call_count == 1
    assert port.last_shutdown is not None
    assert port.last_known_state == PDUPortState.OFF


@patch("time.sleep")
def test_PDUPort__setting_OFF_to_OFF(sleep_mock):
    pdu, port = __pdu_port_mock()

    port.last_shutdown = wanted_last_shutdown = datetime.now()
    port.last_known_state = PDUPortState.OFF

    pdu.get_port_state.return_value = PDUPortState.OFF
    port.set(PDUPortState.OFF)

    sleep_mock.assert_not_called()
    assert port.last_shutdown == wanted_last_shutdown
    assert port.last_known_state == PDUPortState.OFF


def test_PDUPort_eq():
    params = {
        "pdu": "pdu",
        "port_id": 42,
        "label": "label",
        "min_off_time": "min_off_time"
    }

    assert PDUPort(**params) == PDUPort(**params)
    for param in params:
        n_params = dict(params)
        n_params[param] = "modified"
        assert PDUPort(**params) != PDUPort(**n_params)


def test_PDU_defaults():
    config = {"key": "val"}
    pdu = PDU("MyPDU", config)

    assert pdu.name == "MyPDU"
    assert pdu.config == config
    assert pdu.ports == []
    assert pdu.set_port_state(42, PDUPortState.ON) is False
    assert pdu.get_port_state(42) == PDUPortState.UNKNOWN
    assert pdu.get_port_full_state(42) == PDUPortFullState(state=PDUPortState.UNKNOWN)
    assert pdu.power_state == PDUPowerState()
    assert pdu.default_min_off_time == 30

    # No network probing by default
    assert not hasattr(pdu, "network_probe")


def test_PDU_supported_pdus():
    pdus = PDU.supported_pdus()
    assert "dummy" in pdus


def test_PDU_create():
    pdu = PDU.create("dummy", "name", {})
    assert pdu.name == "name"

    with pytest.raises(ValueError):
        PDU.create("invalid", "name", {})


def test_PDU_reserved_port0():
    pdu = PDU.create("dummy", "name", {"ports": ['0', '1', '2', '3']}, reserved_port_ids=[1])
    assert pdu.ports[1].reserved is True
    assert pdu.get_port_state(1) == PDUPortState.ON
    pdu.ports[1].set(PDUPortState.OFF)
    assert pdu.get_port_state(1) == PDUPortState.ON


def test_PDU_reserved_unreserved_port():
    pdu = PDU.create("dummy", "name", {"ports": ['0', '1', '2', '3', '4', '5']}, ['3', '4'])
    assert pdu.ports[3].reserved is True
    assert pdu.ports[4].reserved is True
    assert pdu.reserved_port_ids == {'3', '4'}

    pdu.unreserve_port('3')
    assert pdu.ports[3].reserved is False
    assert pdu.ports[4].reserved is True
    assert pdu.reserved_port_ids == {'4'}

    # Make sure nothing goes wrong when removing an already-removed port
    pdu.ports[3].reserved = False

    pdu.ports[5].reserved = True
    assert pdu.ports[4].reserved is True
    assert pdu.ports[5].reserved is True
    assert pdu.reserved_port_ids == {'4', '5'}


def test_PDUSimpleNetworkProbeMixin():
    class PDUMock(PDUSimpleNetworkProbeMixin):
        driver_name = "PDUMock"

        def __init__(self, name, config, reserved_port_ids=[]):
            assert name == "PDUMock-00:01:02:03:04:05"
            assert config == {"hostname": "10.42.0.1"}
            assert reserved_port_ids == []

    PDUMock.network_probe(ip_address="10.42.0.1", mac_address="00:01:02:03:04:05")
