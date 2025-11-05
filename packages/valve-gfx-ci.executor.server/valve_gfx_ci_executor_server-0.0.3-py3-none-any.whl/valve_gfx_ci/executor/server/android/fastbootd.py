from functools import cached_property

import os

import usb.core
import usb.util

"""
Interact with fastboot-enabled devices

See https://android.googlesource.com/platform/system/core/+/master/fastboot/README.md
for an overview of the protocol.
"""


class FastbootDevice:
    # See https://android.googlesource.com/platform/system/core/+/eclair-release/fastboot/fastboot.c#156
    FASTBOOT_INTERFACE_CLASS = 0xff
    FASTBOOT_INTERFACE_SUBCLASS = 0x42
    FASTBOOT_INTERFACE_PROTOCOL = 0x03

    def __init__(self, device: usb.core.Device, write_chunk=1024*1024):
        self.device = device
        self.write_chunk = write_chunk

        self.ep_read = self.ep_write = None
        for ep in self.intf:
            if usb.util.endpoint_type(ep.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.ep_read = ep
                else:
                    self.ep_write = ep

        assert self.ep_read
        assert self.ep_write

    def release(self):
        self.device._ctx.release_all_interfaces(self.device)

    @cached_property
    def intf(self):
        # Go through all the configurations to find a fastboot interface
        for cfg in self.device:
            intf = usb.util.find_descriptor(cfg,
                                            bInterfaceClass=self.FASTBOOT_INTERFACE_CLASS,
                                            bInterfaceSubClass=self.FASTBOOT_INTERFACE_SUBCLASS,
                                            bInterfaceProtocol=self.FASTBOOT_INTERFACE_PROTOCOL)
            if intf is not None:
                return intf
            else:  # pragma: nocover
                raise ValueError("The device is not a fastboot-compatible")

    def read(self, length, timeout=None):
        return self.ep_read.read(length, timeout=timeout)

    def write(self, data, timeout=None):
        for start in range(0, len(data), self.write_chunk):
            self.ep_write.write(data[start:start+self.write_chunk], timeout=timeout)

    def read_response(self, timeout=None):
        line = self.read(64, timeout=timeout)
        header = bytes(line[:4])
        data = bytes(line[4:])
        return header, data

    def run_cmd(self, cmd, arg=None, timeout=None, wanted_status=b"OKAY"):
        if not isinstance(cmd, bytes):
            cmd = cmd.encode()

        if arg and not isinstance(arg, bytes):
            arg = arg.encode()

        full_cmd = cmd + b":" + arg if arg else cmd
        self.write(full_cmd)

        lines = []
        while True:
            header, data = self.read_response(timeout=timeout)

            lines.append((header, data))

            # Detect the end of the line
            if header in {b'OKAY', b'DATA'}:
                break
            elif header not in {b'INFO'}:  # On failure
                raise ValueError(f"The command '{full_cmd}' failed ({header}) with error '{data}'")

        if wanted_status and header != wanted_status:
            msg = f"The command '{full_cmd}' returned the status '{header}' instead of the expected '{wanted_status}'"
            raise ValueError(msg)

        return lines

    def getvar(self, name):
        if not isinstance(name, bytes):
            name = name.encode()

        # Get all the listed variables, ignoring the last line which simply
        # contains the execution summary
        variables = dict()
        for _, data in self.run_cmd(b'getvar', name)[0:-1]:
            # Look for the last ':'
            if idx := bytes.rfind(data, b':'):
                name = data[0:idx].decode()
                value = data[idx+1:].decode()
                variables[name] = value

        if len(variables) > 1:
            return variables
        elif len(variables) == 1:
            return list(variables.values())[0]
        else:
            return None

    @cached_property
    def variables(self):
        return self.getvar(b"all")

    def upload(self, fp):
        # Check the size
        pos = fp.tell()
        fp.seek(0, os.SEEK_END)
        size = fp.tell() - pos
        fp.seek(pos, os.SEEK_SET)

        # Setup the transfer
        resp = self.run_cmd(b'download:' + f"{size:08x}".encode(), wanted_status=b"DATA")
        assert int(resp[-1][1].decode().rstrip('\x00'), 16) == size

        # Send the file
        while True:
            chunk = fp.read(self.write_chunk)
            if len(chunk) == 0:
                break

            self.ep_write.write(chunk)

        # Wait for the OK
        header, data = self.read_response()
        assert header == b"OKAY"

    def boot(self):
        self.run_cmd(b'boot', timeout=15000)

    @classmethod
    def from_serial(cls, serialno, write_chunk=1024*1024):
        for device in usb.core.find(find_all=True):
            try:
                if device.serial_number != serialno:
                    continue
            except Exception:
                # Ignore errors related to reading the serial number as they
                # are likely related to permission issues and thus not a device
                # we should be caring about
                continue

            return cls(device, write_chunk=write_chunk)

        raise ValueError(f"Couldn't find a device with serialno '{serialno}'")
