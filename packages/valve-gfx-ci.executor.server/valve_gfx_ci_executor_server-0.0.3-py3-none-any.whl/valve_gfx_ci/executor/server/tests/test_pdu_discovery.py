from unittest.mock import patch, MagicMock

from server.pdu.daemon import AsyncPDU
from server.pdu.discovery import PDUDiscovery


# USB discovery

@patch("server.pdu.discovery.USBHubDevice", side_effect=ValueError)
@patch("server.pdu.discovery.USBHubPDU", driver_name="usbhubcustom")
def test_new_usb_device_detected__not_a_usb_hub(hubpdu_mock, hubdev_mock):
    devpath = MagicMock()
    on_discovery = MagicMock()

    PDUDiscovery.new_usb_device_detected(devpath, on_discovery)
    hubdev_mock.assert_called_once_with(devpath)
    hubpdu_mock.assert_not_called()
    on_discovery.assert_not_called()


@patch("server.pdu.discovery.USBHubDevice", return_value=MagicMock(serial="ABCD"))
@patch("server.pdu.discovery.USBHubPDU", driver_name="usbhubcustom")
def test_new_usb_device_detected__with_serial(hubpdu_mock, hubdev_mock):
    devpath = MagicMock()
    on_discovery = MagicMock()

    PDUDiscovery.new_usb_device_detected(devpath, on_discovery)

    hubdev_mock.assert_called_once_with(devpath)
    hubpdu_mock.assert_called_once_with(name="usbhubcustom-ABCD", config={"serial": "ABCD"})
    on_discovery.assert_called_once_with(hubpdu_mock.return_value)


@patch("server.pdu.discovery.USBHubDevice", return_value=MagicMock(serial="", idVendor=0x2109, idProduct=0x0817))
@patch("server.pdu.discovery.USBHubPDU")
def test_new_usb_device_detected__from_known_usbhub(hubpdu_mock, hubdev_mock):
    devpath = MagicMock()
    on_discovery = MagicMock()

    via_usb2_mock = MagicMock(idVendor=0x2109, idProduct=0x2817, busnum=1, devpath="3.2.1")
    via_usb3_mock = MagicMock(idVendor=0x2109, idProduct=0x0817, busnum=2, devpath="4.1")
    hubdev_mock.list.return_value = [via_usb2_mock, via_usb3_mock]

    PDUDiscovery.new_usb_device_detected(devpath, on_discovery)

    hubdev_mock.assert_called_once_with(devpath)
    hubpdu_mock.assert_called_once_with(name="usbhub-VIA-1-3.2.1",
                                        config={"controller": str(hubdev_mock.return_value.controller_path),
                                                "devices": [
                                                    via_usb2_mock.to_USBHubDeviceMatchConfig.return_value.asdict,
                                                    via_usb3_mock.to_USBHubDeviceMatchConfig.return_value.asdict
                                                ]})
    on_discovery.assert_called_once_with(hubpdu_mock.return_value)


@patch("server.pdu.discovery.USBHubDevice", return_value=MagicMock(serial="", idVendor=0x2109, idProduct=0x0817))
@patch("server.pdu.discovery.USBHubPDU")
def test_new_usb_device_detected__from_known_usbhub_but_part_of_known_pdu(hubpdu_mock, hubdev_mock):
    devpath = MagicMock()
    on_discovery = MagicMock()

    via_usb2_mock = MagicMock(idVendor=0x2109, idProduct=0x2817, busnum=1, devpath="3.2.1")
    via_usb3_mock = MagicMock(idVendor=0x2109, idProduct=0x0817, busnum=2, devpath="4.1")
    hubdev_mock.list.return_value = [via_usb2_mock, via_usb3_mock]

    known_pdus = {
        "VIA-1": MagicMock(driver=MagicMock(associated_hubs=[via_usb2_mock, via_usb3_mock]))
    }

    PDUDiscovery.new_usb_device_detected(devpath, on_discovery, known_pdus=known_pdus)

    hubdev_mock.assert_called_once_with(devpath)
    hubpdu_mock.assert_not_called()
    on_discovery.assert_not_called()


@patch("server.pdu.discovery.USBHubDevice", return_value=MagicMock(serial="", idVendor=0x2109, idProduct=0x0817))
@patch("server.pdu.discovery.USBHubPDU")
def test_new_usb_device_detected__from_known_usbhub__incomplete_hub(hubpdu_mock, hubdev_mock):
    devpath = MagicMock()
    on_discovery = MagicMock()

    via_usb2_mock = MagicMock(idVendor=0x2109, idProduct=0x2817, busnum=1, devpath="3.2.1")
    hubdev_mock.list.return_value = [via_usb2_mock]

    PDUDiscovery.new_usb_device_detected(devpath, on_discovery)

    hubdev_mock.assert_called_once_with(devpath)
    hubpdu_mock.assert_called_once_with(name="usbhub-VIA-1-3.2.1",
                                        config={"controller": str(hubdev_mock.return_value.controller_path),
                                                "devices": [
                                                    via_usb2_mock.to_USBHubDeviceMatchConfig.return_value.asdict
                                                ]})
    on_discovery.assert_called_once_with(hubpdu_mock.return_value)


@patch("server.pdu.discovery.USBHubDevice", return_value=MagicMock(serial=""))
@patch("server.pdu.discovery.USBHubPDU", driver_name="usbhubcustom")
def test_new_usb_device_detected__unsupported_hub(hubpdu_mock, hubdev_mock):
    devpath = MagicMock()
    on_discovery = MagicMock()

    PDUDiscovery.new_usb_device_detected(devpath, on_discovery)

    hubdev_mock.assert_called_once_with(devpath)
    hubpdu_mock.assert_not_called()
    on_discovery.assert_not_called()


# Network discovery

known_pdus_fixture = {
    "poe_switch": AsyncPDU(model_name="snmp_poe", pdu_name="poe_switch", config={"hostname": "10.11.12.13"}),
}


def test_handle_network_device_discovery__pdu_already_known():
    on_discovery = MagicMock()
    PDUDiscovery._handle_network_device_discovery(ip_address="10.11.12.13", mac_address="de:ad:be:ef",
                                                  on_discovery=on_discovery, known_pdus=known_pdus_fixture)
    on_discovery.assert_not_called()


@patch("server.pdu.discovery.PDU.supported_pdus")
@patch("server.pdu.discovery.time.sleep")
def test_handle_network_device_discovery__new_pdu_found(sleep_mock, supported_pdus_mock):
    supported_pdus_mock.return_value = {
        "undiscoverable": MagicMock(driver_name="undiscoverable"),
        "raises_ValueError": MagicMock(driver_name="snmp_poe",
                                       network_probe=MagicMock(side_effect=ValueError)),
        "raises_TimeoutError": MagicMock(driver_name="snmp_poe",
                                         network_probe=MagicMock(side_effect=TimeoutError)),
        "wo_ports": MagicMock(driver_name="snmp_poe", return_value=MagicMock(ports=[]),
                              network_probe=MagicMock(return_value=[{"hostname": "10.11.12.14"}])),
        "w_ports": MagicMock(driver_name="snmp_poe",
                             network_probe=MagicMock(return_value=MagicMock(ports=[0, 1, 2, 3]))),
        "unreachable": MagicMock(driver_name="snmp_poe",
                                 network_probe=MagicMock(return_value=MagicMock(ports=[0, 1, 2, 3]))),
    }
    del supported_pdus_mock.return_value["undiscoverable"].network_probe

    on_discovery = MagicMock()
    PDUDiscovery._handle_network_device_discovery(ip_address="10.11.12.14", mac_address="de:ad:be:ef",
                                                  dhcp_client_name="myClientName",
                                                  on_discovery=on_discovery, known_pdus=known_pdus_fixture)

    # Make sure you gave the device some time to settle before probing it
    sleep_mock.assert_called_once_with(1)

    # Make sure the PDU drivers located after a working PDU driver are never probed
    supported_pdus_mock.return_value["unreachable"].network_probe.assert_not_called()

    # Check that all the other drivers were used to probe, until the first valid one
    for driver_name in ["raises_ValueError", "raises_TimeoutError", "wo_ports", "w_ports"]:
        driver = supported_pdus_mock.return_value[driver_name]
        driver.network_probe.assert_called_once_with(ip_address="10.11.12.14", mac_address="de:ad:be:ef",
                                                     dhcp_client_name="myClientName")
        driver.assert_not_called()

    # Make sure the callback is called with the first valid PDU
    on_discovery.assert_called_once_with(supported_pdus_mock.return_value["w_ports"].network_probe.return_value)


@patch.object(PDUDiscovery, "_handle_network_device_discovery")
def test_new_network_device_detected(handle_mock):
    assert PDUDiscovery.new_network_device_detected(key1="value1", key2="value2") is None
    handle_mock.assert_called_once_with(key1="value1", key2="value2")
