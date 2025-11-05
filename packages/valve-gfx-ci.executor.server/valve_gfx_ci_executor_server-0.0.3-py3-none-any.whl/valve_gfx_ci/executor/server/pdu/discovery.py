from collections.abc import Callable
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
import time
import traceback

from . import PDU, logger
from .daemon import AsyncPDU
from .drivers.usbhub import USBHubDevice, USBHubPDU


# Function signature for the PDU discovery callback
PDUDiscoveryCallback = Callable[[PDU], None]


@dataclass(frozen=True)
class USBDevice:
    idVendor: int
    idProduct: int

    def __repr__(self):
        return f"USBDevice<{self.idVendor:04x}:{self.idProduct:04x}>"

    def __str__(self):
        return repr(self)

    @classmethod
    def from_usbhub_device(cls, usbhubdev: USBHubDevice):
        return cls(idVendor=usbhubdev.idVendor, idProduct=usbhubdev.idProduct)


@dataclass(frozen=True)
class KnownUSBHub:
    name: str
    usb2: USBDevice
    usb3: USBDevice = None

    def __repr__(self):
        return f"KnownUSBHub<{self.name}, usb2={self.usb2}, usb3={self.usb3}>"

    def __str__(self):
        return repr(self)

    @classmethod
    def list(cls):
        return [
            # VIA-based hubs such as the MEGA4
            cls(name="VIA", usb2=USBDevice(0x2109, 0x2817), usb3=USBDevice(0x2109, 0x0817)),
            cls(name="Huasheng", usb2=USBDevice(0x214b, 0x7250)),
            cls(name="Terminus", usb2=USBDevice(0x1a40, 0x0101)),
            cls(name="Realtek", usb2=USBDevice(0x0bda, 0x5411), usb3=USBDevice(0x0bda, 0x0411)),
        ]


class PDUDiscovery:
    @classmethod
    def new_usb_device_detected(cls, devpath: Path, on_discovery: PDUDiscoveryCallback,
                                known_pdus: dict[str, AsyncPDU] = dict()) -> None:
        # Check if the device is a valid USB Hub
        try:
            dev = USBHubDevice(devpath)
        except Exception:
            return None

        # Go through the list of known PDUs to identify the hubs we already know
        known_usbhub_hubs = set()
        for known_pdu in known_pdus.values():
            try:
                if hasattr(known_pdu.driver, "associated_hubs"):
                    known_usbhub_hubs.update(known_pdu.driver.associated_hubs)
            except Exception:  # pragma: nocover
                traceback.print_exc()

        # Ignore hubs already part of the known PDUs
        if dev in known_usbhub_hubs:  # pragma: nocover
            logger.info(f"Ignoring {dev} as it is already part of a known PDU")
            return None

        # If we are lucky that the USB Hub has a serial number, then let's try making use of it!
        if dev.serial:
            return on_discovery(USBHubPDU(name=f"{USBHubPDU.driver_name}-{dev.serial}", config={"serial": dev.serial}))

        # Go through the list of hubs, and assign them to a dictionary keyed by (vendor, product) ids
        hubs_by_vidpid = defaultdict(list)
        for hub in USBHubDevice.list():
            hubs_by_vidpid[USBDevice.from_usbhub_device(hub)].append(hub)

        # Go through our list of known hubs
        usbdev = USBDevice.from_usbhub_device(dev)
        for known_hub in KnownUSBHub.list():
            if usbdev == known_hub.usb2 or usbdev == known_hub.usb3:
                usb2_hubs = set(hubs_by_vidpid[known_hub.usb2])
                usb3_hubs = set(hubs_by_vidpid[known_hub.usb3])

                unknown_usb2_hubs = usb2_hubs - known_usbhub_hubs
                unknown_usb3_hubs = usb3_hubs - known_usbhub_hubs

                # Ensure that that USB3 hubs have a **SINGLE AND COMPLETE** unknown hub, as we would otherwise be
                # unable to know which USB2 device goes with which USB3 device...
                #
                # NOTE: USB3 hubs are first enumerated as USB3 before being enumerated as USB2. So if we see a USB2-only
                # hub that was supposed to have a USB3 counterpart, we can assume it was connected through a USB2 hub
                # and it is safe to ignore the USB3 side.
                if ((len(unknown_usb2_hubs) > 0 and len(unknown_usb3_hubs) == 0) or
                        (len(unknown_usb2_hubs) == 1 and len(unknown_usb3_hubs) == 1)):
                    usb2_hub = unknown_usb2_hubs.pop()

                    config = {
                        "controller": str(dev.controller_path),
                        "devices": [usb2_hub.to_USBHubDeviceMatchConfig().asdict]
                    }

                    if known_hub.usb3 and len(unknown_usb3_hubs) == 1:
                        usb3_hub = unknown_usb3_hubs.pop()
                        config["devices"].append(usb3_hub.to_USBHubDeviceMatchConfig().asdict)

                    return on_discovery(USBHubPDU(name=f"usbhub-{known_hub.name}-{usb2_hub.busnum}-{usb2_hub.devpath}",
                                                  config=config))
                else:
                    # The known hub has some matching USB3 devices, and more than one physical hub is present so we
                    # can't know which usb device goes with which one...
                    logger.info(f"The USB Hub {dev} is part of the {known_hub}, but we have more than one matching "
                                "physical USB3 hub. Unplug them all, then re-plug them one by one to enable "
                                "auto-detection")

                    return None

        # Unsupported device
        logger.info(f"Ignoring the unknown USB Hub {dev} as it is not part of a known hub. "
                    "Please report the issue to CI-tron devs!")
        return None

    @classmethod
    def _handle_network_device_discovery(cls, ip_address: str, mac_address: str, on_discovery: PDUDiscoveryCallback,
                                         known_pdus: dict[str, AsyncPDU] = dict(), dhcp_client_name: str = None):
        # Ignore any known PDUs that would reference this IP address in their config
        for known_pdu in known_pdus.values():
            if hostname := known_pdu.config.get('hostname'):
                if hostname == ip_address or hostname.startswith(f"{ip_address}:"):
                    logger.info("New network device detected, but ignored due to being part of a known PDU")
                    return

        client_name = f"{dhcp_client_name or "<no client name>"} @ {ip_address}"

        # First, wait for the device to settle a bit before probing it
        time.sleep(1)

        # Iterate through the list of PDU drivers to find the ones that match the wanted types
        allowed_pdu_drivers = [d for d in PDU.supported_pdus().values() if hasattr(d, "network_probe")]

        # Tell the users what we are about to do
        logger.info((f"New network device detected ({client_name}), trying discovery using "
                     f"{len(allowed_pdu_drivers)} drivers:"))

        for retry in range(2):
            for i, driver in enumerate(allowed_pdu_drivers):
                logger.info(f" * [{i+1}/{len(allowed_pdu_drivers)}] Trying the {driver.driver_name} PDU driver")

                try:
                    pdu = driver.network_probe(ip_address=ip_address, mac_address=mac_address,
                                               dhcp_client_name=dhcp_client_name)
                    if len(pdu.ports) > 0:
                        return on_discovery(pdu)
                except (TimeoutError, ConnectionRefusedError):
                    pass
                except Exception:
                    logger.info(f"  --> driver returned: {traceback.format_exc()}")

            # Some PDUs take up to 30s to initialize after asking for an IP. So let's retry after 30s.
            if retry == 0:  # pragma: nocover
                logger.info(f"No driver found for {client_name}, retrying in 30s...")
                time.sleep(30)
            else:  # pragma: nocover
                logger.info(f"No driver found for {client_name}, aborting...")
                return

    @classmethod
    def new_network_device_detected(cls, **kwargs) -> None:
        # Handle the discovery in a thread since network operations can be slow
        thread = Thread(name=f"PDUDiscovery-{kwargs.get('mac_address', '<noMacAddress>')}",
                        target=cls._handle_network_device_discovery, kwargs=kwargs)
        thread.daemon = True
        thread.start()
