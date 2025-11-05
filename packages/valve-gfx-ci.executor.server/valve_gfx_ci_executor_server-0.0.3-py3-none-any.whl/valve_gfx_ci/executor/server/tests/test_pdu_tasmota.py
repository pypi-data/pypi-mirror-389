from unittest.mock import MagicMock, patch

from server.pdu import PDUPortState, PDUPort
from server.pdu.drivers.tasmota import TasmotaPDU


class TasmotaShellyDeviceMock:
    def get(url):
        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/cm?cmnd=Status":
            ret = {
                "Status": {
                    "Module": 0,
                    "DeviceName": "ShellyPlugSTasmota",
                    "FriendlyName": ["ShellyPlugSTasmota"],
                    "Topic": "tasmota_B4A75B",
                    "ButtonTopic": "0",
                    "Power": 0,
                    "PowerOnState": 3,
                    "LedState": 1,
                    "LedMask": "FFFF",
                    "SaveData": 1,
                    "SaveState": 1,
                    "SwitchTopic": "0",
                    "SwitchMode": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    "ButtonRetain": 0,
                    "SwitchRetain": 0,
                    "SensorRetain": 0,
                    "PowerRetain": 0,
                    "InfoRetain": 0,
                    "StateRetain": 0,
                    "StatusRetain": 0
                }
            }
        elif url == f"{url_prefix}/cm?cmnd=Power1":
            ret = {"POWER": "OFF"}
        elif url == f"{url_prefix}/cm?cmnd=Power1%20ON":
            ret = {"POWER": "ON"}
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.tasmota.TasmotaPDU.requests_retry_session', TasmotaShellyDeviceMock)
def test_tasmota_shelly():
    pdu = TasmotaPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert pdu.num_ports == 1

    assert pdu.ports == [PDUPort(pdu=pdu, port_id="0", label=None)]
    assert pdu.get_port_state("0") == PDUPortState.OFF
    assert pdu.set_port_state("0", PDUPortState.ON)


class TasmotaGosundP1DeviceMock:
    def get(url):
        url_prefix = "http://127.0.0.1"
        if url == f"{url_prefix}/cm?cmnd=Status":
            ret = {
                "Status": {
                    "Module": 0,
                    "DeviceName": "Tasmota",
                    "FriendlyName": ["Tasmota", "", "", ""],
                    "Topic": "tasmota_E9D2B7",
                    "ButtonTopic": "0",
                    "Power": 0,
                    "PowerOnState": 3,
                    "LedState": 1,
                    "LedMask": "FFFF",
                    "SaveData": 1,
                    "SaveState": 1,
                    "SwitchTopic": "0",
                    "SwitchMode": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    "ButtonRetain": 0,
                    "SwitchRetain": 0,
                    "SensorRetain": 0,
                    "PowerRetain": 0,
                    "InfoRetain": 0,
                    "StateRetain": 0,
                    "StatusRetain": 0
                }
            }
        elif url == f"{url_prefix}/cm?cmnd=Power2":
            ret = {"POWER2": "OFF"}
        elif url == f"{url_prefix}/cm?cmnd=Power2%20ON":
            ret = {"POWER2": "ON"}
        else:  # pragma: nocover
            raise ValueError(f"Unexpected URL '{url}'")

        return MagicMock(json=MagicMock(return_value=ret))


@patch('server.pdu.drivers.tasmota.TasmotaPDU.requests_retry_session', TasmotaGosundP1DeviceMock)
def test_tasmota_gosund_p1():
    pdu = TasmotaPDU('MyPDU', config={'hostname': '127.0.0.1'})

    assert pdu.num_ports == 4
    assert pdu.get_port_state("1") == PDUPortState.OFF
    assert pdu.set_port_state("1", PDUPortState.ON)
