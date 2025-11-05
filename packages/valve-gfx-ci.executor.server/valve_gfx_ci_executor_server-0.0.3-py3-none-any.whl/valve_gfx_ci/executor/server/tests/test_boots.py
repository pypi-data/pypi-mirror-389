from unittest.mock import patch, MagicMock
from server.boots import BootService, BootsDHCPD
from server.dhcpd import BootProtocol, CPUArch, DhcpOptions, Firmware, MacAddress, DhcpRequestType53
import server.config as config


@patch("server.boots.BootsTFTPD")
@patch("server.boots.BootsDHCPD")
def create_boot_service(tmp_path, mock_dhcpd, mock_tftpd):
    service = BootService(MagicMock(), private_interface='br0')

    if not config.BOOTS_DISABLE_SERVERS:
        mock_dhcpd.assert_called_with(service, "DHCP Server", 'br0')
        mock_tftpd.assert_called_with(service, "TFTP Server", None, 'br0')

    return service


def test_boot_service(tmp_path):
    create_boot_service(tmp_path)


def test_boot_service_disabled(tmp_path):
    config.BOOTS_DISABLE_SERVERS = True
    try:
        create_boot_service(tmp_path)
    finally:
        config.BOOTS_DISABLE_SERVERS = False


@patch("server.boots.DHCPD.__init__")
def test_dhcpd_static_clients(dhcpd_mock):
    boots = MagicMock()
    dhcp = BootsDHCPD(boots, name="toto", interface="br0")

    m_mac = "00-01-02-03-04-05"
    m_ipaddr = "10.42.0.42"
    m_hostname = "machine1"

    boots.mars.known_ethernet_devices = [MagicMock(mac_address=m_mac, ip_address=m_ipaddr, hostname=m_hostname)]
    assert dhcp.static_clients == [{'mac_addr': MacAddress(m_mac), 'ipaddr': m_ipaddr, 'hostname': m_hostname}]


@patch("server.boots.DHCPD.__init__")
def test_dhcpd_get_response__use_job(dhcpd_mock):
    dhcp = BootsDHCPD(MagicMock(), name="toto", interface="br0")
    dhcp.get_or_assign_ip_for_client = MagicMock(return_value=("10.0.0.42", "new client"))

    wants = dhcp.boots.mars.get_machine_by_id.return_value.handle_dhcp_request.return_value
    assert dhcp.get_response(MagicMock()) == wants


@patch("server.boots.DHCPD.__init__")
@patch("server.boots.PDUDiscovery.new_network_device_detected")
def test_dhcpd_get_response__pdu_discovery(device_detected_mock, dhcpd_mock):
    dhcp = BootsDHCPD(MagicMock(), name="toto", interface="br0")
    dhcp.get_or_assign_ip_for_client = MagicMock(return_value=("10.0.0.42", "new client"))
    dhcp.boots.mars.get_machine_by_id.return_value = None
    dhcp.boots.mars.known_ethernet_devices = []

    request = MagicMock(req_type=DhcpRequestType53.REQUEST, mac_addr=MacAddress("52:54:00:5c:bf:9e"),
                        hostname="mupuf5090x")
    assert dhcp.get_response(request) == DhcpOptions()

    # Check the new_network_device_detected call
    assert len(device_detected_mock.call_args_list) == 1
    args, kwargs = device_detected_mock.call_args_list[0]
    assert len(args) == 0
    on_discovery = kwargs.pop("on_discovery")
    assert kwargs == {
        "ip_address": "10.0.0.42",
        "mac_address": request.mac_addr.as_str,
        "dhcp_client_name": "mupuf5090x",
        "known_pdus": dhcp.boots.mars.known_pdus,
    }

    # Check that the provided callback appends the mac address to the mars "pdu_discovered" method
    pdu = MagicMock()
    assert on_discovery(pdu) is None
    dhcp.boots.mars.pdu_discovered.assert_called_once_with(pdu, request.mac_addr.as_str)


@patch("server.boots.DHCPD.__init__")
def test_dhcpd_get_response__use_defaults(dhcpd_mock):
    dhcp = BootsDHCPD(MagicMock(), name="toto", interface="br0")
    dhcp.logger = MagicMock()
    dhcp.get_or_assign_ip_for_client = MagicMock(return_value=("10.0.0.42", "new client"))

    dhcpd_mock.assert_called_once_with(dhcp, interface="br0")

    # We do not want to check what the job would be doing
    dhcp.boots.mars.get_machine_by_id.return_value.handle_dhcp_request.return_value = None

    request = MagicMock(architecture=CPUArch.X86, firmware=Firmware.BIOS,
                        protocol=BootProtocol.TFTP, mac_addr=MacAddress("00-01-02-03-04-05"))
    assert dhcp.get_response(request) == DhcpOptions()
    dhcp.boots.mars.machine_discovered.assert_called_once_with(
        {
            "id": "00:01:02:03:04:05",
            "mac_address": "00:01:02:03:04:05",
            "base_name": "x86-bios-tftp",
            "ip_address": "10.0.0.42",
            "tags": []
        }, update_if_already_exists=False)
