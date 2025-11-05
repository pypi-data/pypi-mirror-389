from threading import Thread
from pathlib import Path
import socket
import logging
import time
import traceback

import usb.core

from . import config
from .android.fastbootd import FastbootDevice
from .tftpd import TFTPD, TftpRequest, TftpRequestFileNotFoundHandler
from .dhcpd import DHCPD, MacAddress, DhcpOptions, DhcpRequest, DhcpRequestType53
from .logger import logger
from .mars import Mars
from .socketactivation import get_sockets_by_name
from .pdu import PDU
from .pdu.discovery import PDUDiscovery


class BootsDHCPD(DHCPD, Thread):
    def __init__(self, boots, name: str, interface: str):  # pragma: nocover
        self.boots = boots

        Thread.__init__(self, name=name)
        self.daemon = True

        DHCPD.__init__(self, interface=interface)

    @property
    def static_clients(self):
        clients = []
        for device in self.boots.mars.known_ethernet_devices:
            if device.ip_address and device.mac_address:
                clients.append({'mac_addr': MacAddress(device.mac_address),
                                'ipaddr': device.ip_address,
                                'hostname': device.hostname})
        return clients

    def get_response(self, client_request: DhcpRequest) -> DhcpOptions:
        mac_addr = client_request.mac_addr
        ip_address, _ = self.get_or_assign_ip_for_client(mac_addr)
        if client_request.is_valid_netboot_request:
            # Ensure MaRS is aware of this client request
            arch = client_request.architecture.name
            fw = client_request.firmware.name
            protocol = client_request.protocol.name
            dut_data = {
                "id": mac_addr.as_str,
                "mac_address": mac_addr.as_str,
                "base_name": f"{arch}-{fw}-{protocol}".lower(),
                "ip_address": ip_address,
                "tags": []
            }
            self.boots.mars.machine_discovered(dut_data, update_if_already_exists=False)

        # Forward the request to any potential job running on the known DUT associated to this mac address
        if dut := self.boots.mars.get_machine_by_id(mac_addr.as_str, raise_if_missing=False):
            if response := dut.handle_dhcp_request(client_request):
                return response
            else:
                self.logger.info("The associated job did not return a DHCP configuration, use defaults!")
        elif (mac_addr.as_str not in [e.mac_address for e in self.boots.mars.known_ethernet_devices] and
              client_request.req_type == DhcpRequestType53.REQUEST):
            def on_discovery(pdu: PDU) -> None:
                self.boots.mars.pdu_discovered(pdu, mac_addr.as_str)

            PDUDiscovery.new_network_device_detected(ip_address=ip_address,
                                                     mac_address=mac_addr.as_str,
                                                     dhcp_client_name=client_request.hostname,
                                                     on_discovery=on_discovery,
                                                     known_pdus=self.boots.mars.known_pdus)

        # The job did not tell us what to do, so let's fallback to our defaults
        return DhcpOptions()

    def run(self):  # pragma: nocover
        # Use the socket provided by our caller (systemd?), or create or own if none are found
        sock = None
        if sockets := get_sockets_by_name(config.BOOTS_DHCP_IPv4_SOCKET_NAME, socket.AF_INET, socket.SOCK_DGRAM):
            sock = sockets[0]

        self.listen(sock)


class BootsTFTPD(TFTPD, Thread):  # pragma: nocover
    def __init__(self, boots, name, directory, interface):
        self.boots = boots

        Thread.__init__(self, name=name)
        self.daemon = True

        tftp_logger = logging.getLogger(f"{logger.name}.TFTP")
        tftp_logger.setLevel(logging.INFO)
        TFTPD.__init__(self, interface, logger=tftp_logger, netboot_directory=directory)

    def new_request(self, request: TftpRequest):
        self.logger.info(f"Received the {request.opcode.name} TFTP request for {request.filename}")

        # TODO: Make this request in the background?
        if dut := self.boots.mars.get_machine_by_ip_address(request.client_address, raise_if_missing=False):
            if dut.handle_tftp_request(request):
                # We successfully handled the request, nothing else to do!
                opcode_name = request.opcode.name
                self.logger.info(f"--> Processed the {opcode_name},{request.filename} TFTP request by the related job")
                return
            else:
                reason = "Unhandled by job"
        else:
            reason = "No associated DUT"

        # We could not get the executor job to handle the query, handle it ourselves and simply return FileNotFound
        self.logger.info(f"--> Ignore the {request.opcode.name},{request.filename} TFTP request ({reason})")
        TftpRequestFileNotFoundHandler(request, netboot_directory=self.netboot_directory,
                                       default_retries=self.default_retries, timeout=self.timeout,
                                       parent=self)

    def run(self):
        # Use the socket provided by our caller (systemd?), or create or own if none are found
        sock = None
        if sockets := get_sockets_by_name(config.BOOTS_TFTP_IPv4_SOCKET_NAME, socket.AF_INET, socket.SOCK_DGRAM):
            sock = sockets[0]

        self.listen(sock)


class BootsUsbPoller(Thread):  # pragma: nocover
    def __init__(self, boots, name: str):
        self.boots = boots
        self.usb_devices = dict()

        Thread.__init__(self, name=name)
        self.daemon = True

        self.logger = logging.getLogger(f"{logger.name}.Fastbootd")
        self.logger.setLevel(logging.INFO)

    @classmethod
    def find_usbdev_by_bus_address(cls, usbdev) -> Path:
        address = []
        cur = usbdev
        while cur and cur.parent:
            address.insert(0, str(cur.port_number))
            cur = cur.parent

        return Path(f"/sys/bus/usb/devices/{usbdev.bus}-{'.'.join(address)}")

    def new_fastboot_device_found(self, fbdev: FastbootDevice):  # pragma: nocover
        self.logger.info(f"Found a new fastboot device: {repr(fbdev.device)}")

        # Ensure the bootloader is unlocked
        if fbdev.variables.get("unlocked") != "yes":
            try:
                fbdev.run_cmd(b"flashing:unlock")
            except Exception:
                # Ignore errors, we'll just tell users that the device is unusable
                pass

        # Ensure MaRS is aware of this client request
        serialno = fbdev.variables["serialno"]
        mac_addr = MacAddress.from_serial(serialno)
        product_name = fbdev.variables.get("product")
        base_name = product_name or serialno
        ip_address, _ = self.boots.dhcpd.get_or_assign_ip_for_client(mac_addr)
        dut_data = {
            "id": serialno,
            "mac_address": mac_addr.as_str,
            "base_name": f"fastboot-{base_name}".lower(),
            "ip_address": ip_address,
            "tags": []
        }
        self.boots.mars.machine_discovered(dut_data, update_if_already_exists=False)

        # We got everything we wanted from the device, free our lock
        fbdev.release()

        # Notify the DUT that we are ready to boot!
        if dut := self.boots.mars.get_machine_by_id(serialno):
            dut.handle_fastboot_device_added()

    def run(self):
        while True:
            try:
                usb_devices_found = set()
                for usbdev in usb.core.find(find_all=True):
                    usb_devices_found.add(usbdev)

                # Process device removals first
                for usbdev in set(self.usb_devices.keys()) - usb_devices_found:
                    device = self.usb_devices.pop(usbdev)
                    if isinstance(device, FastbootDevice):
                        self.logger.info(f"The fastboot device {repr(usbdev)} got removed")

                # Process devices that were added
                for usbdev in usb_devices_found:
                    # Ignore devices that already existed
                    if usbdev in self.usb_devices:
                        continue

                    self.logger.info(f"New device plugged {repr(usbdev)}")

                    # Check if the device is a fastboot one
                    try:
                        fbdev = FastbootDevice(usbdev)
                        self.usb_devices[usbdev] = fbdev
                        self.new_fastboot_device_found(fbdev)
                        continue
                    except ValueError:
                        # Ignore "The device is not a fastboot-compatible" errors
                        pass

                    # Check if the new device could be a PDU
                    try:
                        PDUDiscovery.new_usb_device_detected(self.find_usbdev_by_bus_address(usbdev),
                                                             known_pdus=self.boots.mars.known_pdus,
                                                             on_discovery=self.boots.mars.pdu_discovered)
                    except Exception:
                        traceback.print_exc()

                    # Just add the device to the list, but without any associated object
                    self.usb_devices[usbdev] = None
            except Exception:
                traceback.print_exc()
            finally:
                time.sleep(1)


class BootService:
    def __init__(self, mars: Mars,
                 private_interface: str = None):
        self.mars = mars
        self.private_interface = private_interface or config.PRIVATE_INTERFACE

        # Do not start the servers
        if config.BOOTS_DISABLE_SERVERS:
            self.dhcpd = self.tftpd = self.fastbootd = None
            return

        self.dhcpd = BootsDHCPD(self, "DHCP Server", self.private_interface)
        self.dhcpd.dns_servers = [self.dhcpd.ip]
        self.dhcpd.start()

        self.tftpd = BootsTFTPD(self, "TFTP Server", None, self.private_interface)
        self.tftpd.start()

        self.usb = BootsUsbPoller(self, "USB Device Poller")
        self.usb.start()
