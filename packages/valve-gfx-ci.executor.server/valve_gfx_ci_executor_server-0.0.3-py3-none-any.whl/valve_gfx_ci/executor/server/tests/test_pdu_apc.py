from unittest.mock import MagicMock
import pytest

from server.pdu import PDUPowerState, PDUPowerChannel
from server.pdu.drivers.apc import ApcMasterswitchPDU
from server.tests.test_pdu_basesnmp import _reset_easysnmp_mock


@pytest.fixture(autouse=True)
def reset_easysnmp_mock(monkeypatch):
    global Session, time_sleep
    Session, time_sleep = _reset_easysnmp_mock(monkeypatch)


def test_ApcMasterswitchPDU_defaults():
    pdu = ApcMasterswitchPDU("APC", {"hostname": "127.0.0.1"})
    assert pdu.voltage == 230
    assert pdu.power_factor == 0.9


expected_channel = PDUPowerChannel(instant_power=436.8)


def check_power_state(phases: int, banks: int, has_total: bool = False, voltage: float = 208,
                      power_factor: float = 0.5, report_count: int = None) -> PDUPowerState:
    walk_mock = Session.return_value.walk
    get_mock = Session.return_value.get
    walk_mock.return_value = [MagicMock(value="42")] * (report_count or (has_total + phases + banks))

    pdu = ApcMasterswitchPDU("APC", {"hostname": "127.0.0.1", "voltage": str(voltage),
                                     "power_factor": str(power_factor)})

    # Pre-load the phase count and check the reporting
    get_mock.return_value = MagicMock(value=str(phases))
    assert pdu.power_phase_count == phases
    get_mock.assert_called_with(pdu.power_phase_count_oid)

    # Pre-load the bank count and check the reporting
    get_mock.return_value = MagicMock(value=str(banks))
    assert pdu.power_bank_count == banks
    get_mock.assert_called_with(pdu.power_bank_count_oid)

    # Check that the config parameters got set
    assert pdu.voltage == 208
    assert pdu.power_factor == 0.5

    # Generate the power state report
    state = pdu.power_state

    # Check all the generated channels
    expected_power = voltage * 42 * power_factor / 10
    expected_energy = None
    for name, channel in state.power_channels.items():
        assert channel.instant_power == expected_power
        assert channel.energy == expected_energy

    return state


def test_ApcMasterswitchPDU_power_state__invalid_report_count():
    with pytest.raises(ValueError) as exc:
        print(check_power_state(phases=1, banks=0, report_count=3))
    assert "Unexpected amount of load entries. Expected 1 or 2 entries but got 3" in str(exc)


def test_ApcMasterswitchPDU_power_state__no_power_reporting():
    state = check_power_state(phases=0, banks=0, has_total=False)

    assert state.total_power is None
    assert len(state.power_channels) == 0


def test_ApcMasterswitchPDU_power_state__single_phase():
    state = check_power_state(phases=1, banks=0, has_total=False)

    assert state.total_power == expected_channel
    assert len(state.power_channels) == 0


def test_ApcMasterswitchPDU_power_state__single_bank():
    state = check_power_state(phases=0, banks=1, has_total=False)

    assert state.total_power == expected_channel
    assert len(state.power_channels) == 0


def test_ApcMasterswitchPDU_power_state__dual_bank():
    state = check_power_state(phases=0, banks=2, has_total=False)

    assert state.total_power == expected_channel * 2
    assert list(state.power_channels.keys()) == ["Bank #1", "Bank #2"]


def test_ApcMasterswitchPDU_power_state__single_phase_dual_bank():
    state = check_power_state(phases=1, banks=2, has_total=False)

    assert state.total_power == expected_channel
    assert list(state.power_channels.keys()) == ["Bank #1", "Bank #2"]


def test_ApcMasterswitchPDU_power_state__three_phases_and_six_banks():
    state = check_power_state(phases=3, banks=6, has_total=False)

    assert state.total_power == expected_channel * 3
    assert list(state.power_channels.keys()) == ["Phase #1", "Phase #2", "Phase #3",
                                                 "Bank #1", "Bank #2", "Bank #3", "Bank #4", "Bank #5", "Bank #6"]


def test_ApcMasterswitchPDU_power_state__three_phases_and_total():
    state = check_power_state(phases=3, banks=0, has_total=True)

    assert state.total_power == expected_channel
    assert list(state.power_channels.keys()) == ["Phase #1", "Phase #2", "Phase #3"]
