from unittest.mock import MagicMock, patch
import pytest

from server.pdu import PDUPortState, PDUPort, PDUPortFullState
from server.pdu.drivers.shelly import ShellyPDU


class ShellyPlugMock:
    def get(url, timeout=None):
        assert timeout == 1

        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/shelly":
            ret = {
                "type": "SHPLG2-1",
                "mac": "C45BBE49EAA7",
                "auth": False,
                "fw": "20221027-102248/v1.12.1-ga9117d3",
                "discoverable": True,
                "num_outputs": 1,
                "num_meters": 1
            }
        elif url == f"{url_prefix}/settings/relay/0":
            ret = {
                "name": None,
                "appliance_type": "Computer",
                "ison": True,
                "has_timer": False,
                "default_state": "last",
                "auto_on": 0,
                "auto_off": 0,
                "schedule": False,
                "schedule_rules": [],
                "max_power": 3500
            }
        elif url == f"{url_prefix}/relay/0":
            ret = {
                "ison": True,
                "has_timer": False,
                "timer_started": 0,
                "timer_duration": 0,
                "timer_remaining": 0,
                "overpower": False,
                "source": "input"
            }
        elif url == f"{url_prefix}/relay/0?turn=off":
            ret = {
                "ison": False,
                "has_timer": False,
                "timer_started": 0,
                "timer_duration": 0,
                "timer_remaining": 0,
                "overpower": False,
                "source": "http"
            }
        elif url == f"{url_prefix}/meter/0":
            ret = {
                "power": 218.11,
                "overpower": 0,
                "is_valid": True,
                "timestamp": 1684923696,
                "counters": [
                    193.84,
                    195.551,
                    201.603
                ],
                "total": 6164469
            }
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.shelly.ShellyPDU.requests_retry_session', ShellyPlugMock)
def test_shelly_plug():
    pdu = ShellyPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert pdu.gen == 1
    assert pdu.num_ports == 1

    assert pdu.ports == [PDUPort(pdu=pdu, port_id="0", label=None)]
    assert pdu.get_port_state("0") == PDUPortState.ON
    assert pdu.set_port_state("0", PDUPortState.OFF)
    assert pdu.get_port_full_state("0") == PDUPortFullState(state=PDUPortState.ON,
                                                            instant_power=218.11,
                                                            energy=None)


class ShellyPlugSMock:
    def get(url, timeout=None):
        assert timeout == 1

        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/shelly":
            ret = {
                "type": "SHPLG-S",
                "mac": "7C87CEB519DB",
                "auth": False,
                "fw": "20230503-101129/v1.13.0-g9aed950",
                "discoverable": True,
                "longid": 1,
                "num_outputs": 1,
                "num_meters": 1
            }
        elif url == f"{url_prefix}/settings/relay/0":
            ret = {
                "name": "My channel",
                "appliance_type": "General",
                "ison": True,
                "has_timer": False,
                "default_state": "off",
                "auto_on": 0.00,
                "auto_off": 0.00,
                "schedule": False,
                "schedule_rules": [],
                "max_power": 1800
            }
        elif url == f"{url_prefix}/relay/0":
            ret = {
                "ison": True,
                "has_timer": False,
                "timer_started": 0,
                "timer_duration": 0,
                "timer_remaining": 0,
                "overpower": False,
                "source": "http",
            }
        elif url == f"{url_prefix}/relay/0?turn=off":
            ret = {
                "ison": False,
                "has_timer": False,
                "timer_started": 0,
                "timer_duration": 0,
                "timer_remaining": 0,
                "overpower": False,
                "source": "http",
            }
        elif url == f"{url_prefix}/meter/0":
            ret = {
                "power": 95.55,
                "overpower": 0,
                "is_valid": True,
                "timestamp": 1684923780,
                "counters": [
                    107.304,
                    90.008,
                    86.23
                ],
                "total": 2893636
            }
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.shelly.ShellyPDU.requests_retry_session', ShellyPlugSMock)
def test_shelly_plug_s():
    pdu = ShellyPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert pdu.gen == 1
    assert pdu.num_ports == 1

    assert pdu.ports == [PDUPort(pdu=pdu, port_id="0", label="My channel")]
    assert pdu.get_port_state("0") == PDUPortState.ON
    assert pdu.set_port_state("0", PDUPortState.OFF)

    assert pdu.get_port_full_state("0") == PDUPortFullState(state=PDUPortState.ON,
                                                            instant_power=95.55,
                                                            energy=None)


class Shelly1LMock:
    def get(url, timeout=None):
        assert timeout == 1

        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/shelly":
            ret = {
                "type": "SHSW-L",
                "mac": "98CDAC1EB380",
                "auth": False,
                "fw": "20221027-091704/v1.12.1-ga9117d3",
                "discoverable": True,
                "longid": 1,
                "num_inputs": 2,
                "num_outputs": 1,
                "num_meters": 1
            }
        elif url == f"{url_prefix}/settings/relay/0":
            ret = {
                "name": None,
                "appliance_type": "General",
                "ison": True,
                "has_timer": False,
                "default_state": "last",
                "btn1_type": "edge",
                "btn1_reverse": 0,
                "btn2_type": "toggle",
                "btn2_reverse": 0,
                "swap_inputs": False,
                "auto_on": 0,
                "auto_off": 0,
                "schedule": False,
                "schedule_rules": []
            }
        elif url == f"{url_prefix}/relay/0":
            ret = {
                "ison": True,
                "has_timer": False,
                "timer_started": 0,
                "timer_duration": 0,
                "timer_remaining": 0,
                "source": "http"
            }
        elif url == f"{url_prefix}/relay/0?turn=off":
            ret = {
                "ison": False,
                "has_timer": False,
                "timer_started": 0,
                "timer_duration": 0,
                "timer_remaining": 0,
                "source": "http"
            }
        elif url == f"{url_prefix}/meter/0":
            return MagicMock(text="Not Found", json=MagicMock(side_effect=ValueError))
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.shelly.ShellyPDU.requests_retry_session', Shelly1LMock)
def test_shelly_1L():
    pdu = ShellyPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert pdu.gen == 1
    assert pdu.num_ports == 1

    assert pdu.ports == [PDUPort(pdu=pdu, port_id="0", label=None)]
    assert pdu.get_port_state("0") == PDUPortState.ON
    assert pdu.set_port_state("0", PDUPortState.OFF)

    assert pdu.get_port_full_state("0") == PDUPortFullState(state=PDUPortState.ON)


class ShellyPlus2PMMock:
    def get(url, timeout=None):
        assert timeout == 1

        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/shelly":
            ret = {
                "name": "My ShellyPlus2PM",
                "id": "shellyplus2pm-c049ef860c58",
                "mac": "C049EF860C58",
                "model": "SNSW-102P16EU",
                "gen": 2,
                "fw_id": "20220527-091739/0.10.2-beta4-gecc3a61",
                "ver": "0.10.2-beta4",
                "app": "Plus2PM",
                "auth_en": False,
                "auth_domain": None,
                "profile": "switch"
            }
        elif url == f"{url_prefix}/rpc/Switch.GetConfig?id=0":
            ret = {
                "id": 0,
                "name": "Channel1",
                "in_mode": "follow",
                "initial_state": "on",
                "auto_on": False,
                "auto_on_delay": 60.00,
                "auto_off": False,
                "auto_off_delay": 60.00,
                "power_limit": 2800,
                "voltage_limit": 280,
                "current_limit": 10.000
            }
        elif url == f"{url_prefix}/rpc/Switch.GetConfig?id=1":
            ret = {
                "id": 1,
                "name": "Channel2",
                "in_mode": "follow",
                "initial_state": "off",
                "auto_on": False,
                "auto_on_delay": 60.00,
                "auto_off": False,
                "auto_off_delay": 60.00,
                "power_limit": 2800,
                "voltage_limit": 280,
                "current_limit": 10.000
            }
        elif url == f"{url_prefix}/rpc/Switch.GetStatus?id=0":
            ret = {
                "id": 0,
                "source": "HTTP",
                "output": False,
                "apower": 0.0,
                "voltage": 235.6,
                "current": 0.000,
                "pf": 0.00,
                "aenergy": {
                    "total": 4120.351,
                    "by_minute": [0.000, 0.000, 0.000],
                    "minute_ts": 1684838501
                },
                "temperature": {
                    "tC": 27.7,
                    "tF": 81.9
                }
            }
        elif url == f"{url_prefix}/rpc/Switch.GetStatus?id=1":
            ret = {
                "id": 1,
                "source": "HTTP",
                "output": True,
                "apower": 0.0,
                "voltage": 240.6,
                "current": 0.000,
                "pf": 0.00,
                "aenergy": {
                    "total": 5120.5,
                    "by_minute": [0.000, 0.000, 0.000],
                    "minute_ts": 1684838501
                },
                "temperature": {
                    "tC": 27.7,
                    "tF": 81.9
                }
            }
        elif url == f"{url_prefix}/rpc/Switch.Set?id=0&on=true":
            ret = {"was_on": False}
        elif url == f"{url_prefix}/rpc/Switch.Set?id=1&on=false":
            ret = {"was_on": True}
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.shelly.ShellyPDU.requests_retry_session', ShellyPlus2PMMock)
def test_shelly_plus_2pm():
    pdu = ShellyPDU('MyPDU', config={'hostname': '127.0.0.1'}, reserved_port_ids=['1'])

    assert pdu.gen == 2
    assert pdu.num_ports == 2

    assert pdu.ports == [PDUPort(pdu=pdu, port_id="0", label="Channel1"),
                         PDUPort(pdu=pdu, port_id="1", label="Channel2")]
    assert pdu.get_port_state("0") == PDUPortState.OFF
    assert pdu.get_port_state("1") == PDUPortState.ON

    assert pdu.set_port_state("0", PDUPortState.ON)
    assert pdu.set_port_state("1", PDUPortState.OFF)

    assert pdu.get_port_full_state("1") == PDUPortFullState(state=PDUPortState.ON,
                                                            instant_power=0.0,
                                                            energy=18433800)


class ShellyPlusPlugSMock:
    def get(url, timeout=None):
        assert timeout == 1

        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/shelly":
            ret = {
                "name": "My ShellyPlusPlugS",
                "id": "shellyplusplugs-80646fd61f2c",
                "mac": "80646FD61F2C",
                "model": "SNPL-00112EU",
                "gen": 2,
                "fw_id": "20230510-081027/0.14.4-g4da93ee",
                "ver": "0.14.4",
                "app": "PlusPlugS",
                "auth_en": False,
                "auth_domain": None,
            }
        elif url == f"{url_prefix}/rpc/Switch.GetConfig?id=0":
            ret = {
                "id": 0,
                "name": "Channel",
                "initial_state": "off",
                "auto_on": False,
                "auto_on_delay": 60,
                "auto_off": False,
                "auto_off_delay": 60,
                "power_limit": 2500,
                "voltage_limit": 280,
                "current_limit": 12
            }
        elif url == f"{url_prefix}/rpc/Switch.GetStatus?id=0":
            ret = {
                "id": 0,
                "source": "init",
                "output": False,
                "apower": 0,
                "voltage": 0,
                "current": 0,
                "aenergy": {
                    "total": 0,
                    "by_minute": [0, 0, 0],
                    "minute_ts": 1684910834
                },
                "temperature": {
                    "tC": 36.3,
                    "tF": 97.4
                }
            }
        elif url == f"{url_prefix}/rpc/Switch.Set?id=0&on=true":
            ret = {"was_on": False}
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.shelly.ShellyPDU.requests_retry_session', ShellyPlusPlugSMock)
def test_shelly_plus_plug_s():
    pdu = ShellyPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert pdu.gen == 2
    assert pdu.num_ports == 1

    assert pdu.ports == [PDUPort(pdu=pdu, port_id="0", label="Channel")]
    assert pdu.get_port_state("0") == PDUPortState.OFF
    assert pdu.set_port_state("0", PDUPortState.ON)


class ShellyFutureDeviceMock:
    def get(url, timeout=None):
        assert timeout == 1

        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/shelly":
            ret = {
                "name": "My ShellyPlusPlus2PM",
                "id": "shellyplusplus2pm-c049ef860c58",
                "mac": "C049EF860C58",
                "model": "SNSW-102P16EU",
                "gen": 2,
                "fw_id": "20220527-091739/0.10.2-beta4-gecc3a61",
                "ver": "0.10.2-beta4",
                "app": "PlusPlus2PM",
                "auth_en": False,
                "auth_domain": None,
                "profile": "switch"
            }
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.shelly.ShellyPDU.requests_retry_session', ShellyFutureDeviceMock)
def test_shelly_future_device():
    with pytest.raises(ValueError) as excinfo:
        ShellyPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert "Unknown Shelly device: gen=2, type=None, model=SNSW-102P16EU, app=PlusPlus2PM" in str(excinfo.value)


@patch("server.pdu.drivers.shelly.ShellyPDU.__new__")
def test_shelly_network_probe__with_dhcp_client_name(init_mock):
    ShellyPDU.network_probe(ip_address="10.42.0.1", mac_address="00:01:02:03:04:05",
                            dhcp_client_name="shellyplusplugs-80646fd61f2c")
    init_mock.assert_called_once_with(ShellyPDU, "shellyplusplugs-80646fd61f2c", config={"hostname": "10.42.0.1"})


@patch("server.pdu.drivers.shelly.ShellyPDU.__new__")
def test_shelly_network_probe__without_dhcp_client_name(init_mock):
    ShellyPDU.network_probe(ip_address="10.42.0.1", mac_address="00:01:02:03:04:05")
    init_mock.assert_called_once_with(ShellyPDU, "shelly-00:01:02:03:04:05", config={"hostname": "10.42.0.1"})
