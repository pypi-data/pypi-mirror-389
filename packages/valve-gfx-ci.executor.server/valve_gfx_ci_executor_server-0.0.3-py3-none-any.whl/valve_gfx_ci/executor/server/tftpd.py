#
# The MIT License (MIT)
#
# Copyright (c) 2015 PsychoMario (imported from PyPXE)
# Copyright (c) 2023-2024 Valve Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from enum import Enum
from functools import cached_property
from dataclasses import dataclass
from threading import Thread

import socket
import struct
import os
import time
import traceback
import logging
import math


class TftpRequestOpcode(Enum):
    RRQ = 1   # Read request
    WRQ = 2   # Write request
    DATA = 3
    ACK = 4   # Acknowledgment
    ERROR = 5


@dataclass
class TftpRequest:
    server_ip: str
    client_address: str
    client_port: int
    message: bytes

    @cached_property
    def opcode(self) -> TftpRequestOpcode:
        [opcode] = struct.unpack('!H', self.message[:2])
        return TftpRequestOpcode(opcode)

    @cached_property
    def filename(self):
        if self.opcode in [TftpRequestOpcode.RRQ, TftpRequestOpcode.WRQ]:
            filename = self.message[2:].split(b'\x00')[0].decode('ascii')
            if not filename.startswith("/"):
                filename = "/" + filename
            return filename

    @cached_property
    def filemode(self) -> str:
        if self.opcode in [TftpRequestOpcode.RRQ, TftpRequestOpcode.WRQ]:
            return self.message[2:].split(b'\x00')[1].decode('ascii').lower()

    def __str__(self):
        extra = ""
        if self.opcode in [TftpRequestOpcode.RRQ, TftpRequestOpcode.WRQ]:
            extra = f" - {self.filename} ({self.filemode})"

        return f"<TftpRequest - {self.client_address}:{self.client_port} - {self.opcode.name}{extra}>"


class PathTraversalException(Exception):
    pass


def normalize_path(base, filename):
    '''
        Join and normalize a base path and filename.

       `base` may be relative, in which case it's converted to absolute.

        Args:
            base (str): Base path
            filename (str): Filename (optionally including path relative to
                            base)

        Returns:
            str: The joined and normalized path

        Raises:
            PathTraversalException: if an attempt to escape the base path is
                                    detected
    '''
    abs_path = os.path.abspath(base)
    joined = os.path.join(abs_path, filename)
    normalized = os.path.normpath(joined)
    if normalized.startswith(os.path.join(abs_path, '')):
        return normalized
    raise PathTraversalException('Path Traversal detected')


class TftpRequestHandler(Thread):
    def __init__(self, new_client: TftpRequest,
                 netboot_directory: str = ".",
                 default_retries: int = 10,
                 timeout: int = 1,
                 parent=None):
        super().__init__(name='TftpRequestHandler')

        self.server_ip = new_client.server_ip
        self.client_address = new_client.client_address
        self.client_port = new_client.client_port
        self.message = new_client.message

        self.netboot_directory = netboot_directory
        self.default_retries = default_retries
        self.timeout = timeout
        self.parent = parent

        self.retries = default_retries
        self.block = 1
        self.blksize = 512
        self.sent_time = float('inf')
        self.dead = False
        self.fh = None
        self.filename = ''
        self.wrap = 0
        self.arm_wrap = False

        self.logger = logging.getLogger(f"TFTPDClient.{self.client_address}:{self.client_port}")
        self.logger.debug('Receiving request...')

        self.start()

    @property
    def address(self):
        return (self.client_address, self.client_port)

    def send_block(self):
        '''
            Sends the next block of data, setting the timeout and retry
            variables accordingly.
        '''

        # We never started a transfer, abort!
        if self.block == 0:
            self.complete()
            return

        data = b""
        try:
            self.fh.seek(self.blksize * (self.block - 1))
            while len(data) < self.blksize:
                chunk = self.fh.read(self.blksize - len(data))
                if len(chunk) == 0:
                    break
                data += chunk
        except Exception:
            self.logger.error('Error while reading block {0}'.format(self.block))
            self.dead = True
            return
        # opcode 3 == DATA, wraparound block number
        response = struct.pack('!HH', TftpRequestOpcode.DATA.value, self.block % 65536)
        response += data
        self.sock.sendto(response, self.address)
        self.logger.debug('Sending block {0}/{1}'.format(self.block, self.lastblock))
        self.retries -= 1
        self.sent_time = time.time()

    def no_ack(self):
        '''Determines if we timed out waiting for an ACK from the client.'''
        if self.sent_time + self.timeout < time.time():
            return True
        return False

    def no_retries(self):
        '''Determines if the client ran out of retry attempts.'''
        if not self.retries:
            return True
        return False

    def valid_mode(self):
        '''Determines if the file read mode octet; if not, send an error.'''
        mode = self.message.split(b'\x00')[1]
        if mode == b'octet':
            return True
        self.send_error(5, 'Mode {0} not supported'.format(mode))
        return False

    def load_file(self, filename):
        '''
            Determines if the file exists under the netboot_directory,
            and if it is a file; if not, send an error.
        '''
        try:
            filename = normalize_path(self.parent.netboot_directory, filename)
        except PathTraversalException:
            return False

        # check that the file is really a file, not a rogue FIFO, socket or
        # a device node lurking inside TFTP dir
        if not os.path.lexists(filename) or not os.path.isfile(filename):
            return False

        try:
            self.fh = open(filename, 'rb')
        except IOError:
            return False

        self.filename = filename

        self.fh.seek(0, os.SEEK_END)
        self.filesize = self.fh.tell()
        self.fh.seek(0, os.SEEK_SET)

        self.logger.info('File {0} ({1} bytes) requested'.format(self.filename, self.filesize))

        return True

    def parse_options(self):
        '''
            Extracts the options sent from a client; if any, calculates the last
            block based on the filesize and blocksize.
        '''
        options = self.message.split(b'\x00')[2: -1]
        options = dict(zip((i.decode('ascii') for i in options[0::2]), map(int, options[1::2])))
        self.changed_blksize = 'blksize' in options
        if self.changed_blksize:
            self.blksize = options['blksize']
        self.lastblock = math.ceil(self.filesize / float(self.blksize))
        self.tsize = True if 'tsize' in options else False
        if self.filesize > (2 ** 16) * self.blksize:
            self.logger.warning('Request too big, attempting transfer anyway.')
            self.logger.debug('Details: Filesize {0} is too big for blksize {1}.'.format(self.filesize, self.blksize))
        if len(options):
            # we need to know later if we actually had any options
            self.block = 0
            return True
        else:
            return False

    def reply_options(self):
        '''Acknowledges any options received.'''
        # only called if options, so send them all
        response = struct.pack("!H", 6)
        if self.changed_blksize:
            response += b'blksize' + b'\x00'
            response += str(self.blksize).encode('ascii') + b'\x00'
        if self.tsize:
            response += b'tsize' + b'\x00'
            response += str(self.filesize).encode('ascii') + b'\x00'

        self.sent_time = time.time()
        self.sock.sendto(response, (self.client_address, self.client_port))

    def new_request(self):
        '''
            When receiving a read request from the parent socket, open our
            own socket and check the read request; if we don't have any options,
            send the first block.
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.server_ip, 0))

        # Set a timeout to the socket so that we don't wait eternally
        self.sock.settimeout(self.timeout)

        if not self.valid_mode():
            # some clients just ACK the error (wrong code?)
            # so forcefully shutdown
            self.complete()
            return

        filename = self.message.split(b'\x00')[0].decode('ascii')
        if not filename.startswith("/"):
            filename = "/" + filename

        self.logger.info(f"Client requested {filename}")

        if not self.load_file(filename):
            self.send_error(1, 'File Not Found', filename=filename)
            self.complete()
            return

        if not self.parse_options():
            # no options received so start transfer
            if self.block == 1:
                self.send_block()
            return
        self.reply_options()  # we received some options so ACK those first

    def send_error(self, code=1, message='File Not Found', filename=''):
        '''
            Sends an error code and string to a client. See RFC1350, page 10 for
            details.

            Value   Meaning
            =====   =======
            0       Not defined, see error message (if any).
            1       File not found.
            2       Access violation.
            3       Disk full or allocation exceeded.
            4       Illegal TFTP operation.
            5       Unknown transfer ID.
            6       File already exists.
            7       No such user.
        '''
        response = struct.pack('!H', TftpRequestOpcode.ERROR.value)  # error opcode
        response += struct.pack('!H', code)  # error code
        response += message.encode('ascii')
        response += b'\x00'
        self.sock.sendto(response, self.address)
        self.logger.info('Sending {0}: {1} {2}'.format(code, message, filename))

    def complete(self):
        '''
            Closes a file and socket after sending it
            and marks ourselves as dead to be cleaned up.
        '''
        try:
            if self.fh and not self.fh.closed:
                self.fh.close()
        except Exception:
            self.logger.warning(traceback.format_exc())

        if self.sock and self.sock.fileno() >= 0:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                # We ignore errors here as we were just being nice to the other
                # end and they may already have closed their socket
                pass

            try:
                self.sock.close()
            except Exception:
                self.logger.warning(traceback.format_exc())

        self.dead = True

    def handle(self):
        '''Takes the message from the parent socket and act accordingly.'''
        # if addr not in ongoing, call this, else ready()
        [opcode] = struct.unpack('!H', self.message[:2])
        if opcode == TftpRequestOpcode.RRQ.value:
            self.message = self.message[2:]
            self.new_request()
        elif opcode == TftpRequestOpcode.ACK.value:
            [block] = struct.unpack('!H', self.message[2:4])
            if block == 0 and self.arm_wrap:
                self.wrap += 1
                self.arm_wrap = False
            if block == 32768:
                self.arm_wrap = True
            if block < self.block % 65536:
                self.logger.warning('Ignoring duplicated ACK received for block {0}'.format(self.block))
            elif block > self.block % 65536:
                self.logger.warning('Ignoring out of sequence ACK received for block {0}'.format(self.block))
            elif block + self.wrap * 65536 == self.lastblock:
                if self.filesize % self.blksize == 0:
                    self.block = block + 1
                    self.send_block()
                self.logger.info('Completed sending {0}'.format(self.filename))
                self.complete()
            else:
                self.block = block + 1
                self.retries = self.default_retries
                self.send_block()
        elif opcode == TftpRequestOpcode.WRQ.value:
            # write request
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.ip, 0))
            # used by select() to find ready clients
            self.sock.parent = self
            # send error
            self.send_error(4, 'Write support not implemented')
            self.dead = True
        elif opcode == TftpRequestOpcode.ERROR.value:
            [error_code] = struct.unpack('!H', self.message[2:4])
            error_msg = self.message[4:].split(b'\x00')[0].decode('ascii')
            self.logger.info(f'Client error {error_code}: {error_msg}')
            self.complete()
        else:
            self.logger.info(f'Invalid opcode {opcode}: {error_msg}')
            self.complete()

    def run(self):
        # Handle the read/write request
        self.handle()

        while not self.dead:
            try:
                self.message = self.sock.recv(1024)
                self.handle()
            except TimeoutError:
                # Timed out waiting for the ACK
                if self.no_retries():
                    # We ran out of tries... Abort!
                    self.logger.info('Timeout while sending {0}'.format(self.filename))
                    self.complete()
                else:
                    # re-send the block!
                    self.send_block()


class TftpRequestFileNotFoundHandler(TftpRequestHandler):
    def load_file(self, filename):
        return False


class TFTPD:
    '''
        This class implements a read-only TFTP server
        implemented from RFC1350 and RFC2348
    '''

    def __init__(self, interface, client=TftpRequestHandler, **server_settings):
        self.interface = interface
        self.client = client

        self.ip = server_settings.get('ip', '0.0.0.0')
        self.port = int(server_settings.get('port', 69))
        self.netboot_directory = server_settings.get('netboot_directory', '.')
        self.logger = server_settings.get('logger', None)
        self.default_retries = server_settings.get('default_retries', 10)
        self.timeout = server_settings.get('timeout', 1)

        # setup logger
        if self.logger is None:
            self.logger = logging.getLogger('TFTP')
            self.logger.propagate = False
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def new_request(self, request: TftpRequest):
        self.client(request, netboot_directory=self.netboot_directory,
                    default_retries=self.default_retries, timeout=self.timeout)

    def listen(self, sock=None):
        '''This method listens for incoming requests.'''
        def main_loop(server_sock):
            while True:
                message, address = server_sock.recvfrom(1024)
                try:
                    self.new_request(TftpRequest(server_ip=self.ip, client_address=address[0],
                                                 client_port=address[1], message=message))
                except Exception:
                    self.logger.error(traceback.format_exc())

        # Use the provided socket if specified, or create our own
        if sock:
            main_loop(sock)
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:      # IPv4 UDP socket
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)      # Allow quick rebinding after restart
                if self.interface:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,  # Only listen to the wanted iface
                                    self.interface.encode())
                sock.bind((self.ip, self.port))
                main_loop(sock)
