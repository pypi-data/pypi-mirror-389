from pathlib import Path
from pydantic.dataclasses import dataclass
from subprocess import run, PIPE, STDOUT
from urllib.parse import urlparse

import os
import random
import select
import signal
import tempfile

from . import config


def create_tmp_raw_backing(size: int) -> Path:
    os.makedirs(config.EXECUTOR_NBD_ROOT, exist_ok=True)

    fd, path = tempfile.mkstemp(dir=config.EXECUTOR_NBD_ROOT)
    os.unlink(path)
    os.ftruncate(fd, size)
    return Path("/proc/") / str(os.getpid()) / "fd" / str(fd)


@dataclass(config=dict(extra="forbid"))
class Nbd:
    name: str
    backing: Path
    backing_read_only: bool

    export_as_read_only: bool = False
    max_connections: int = 4

    def _qemu_nbd_args(self, tcp_port, pid_file):
        params = ["qemu-nbd", "-f", "raw", "-p", str(tcp_port), "--fork", "--pid-file", pid_file,
                  "--shared", str(self.max_connections), '--persistent']
        if self.backing_read_only and not self.export_as_read_only:
            params.append("-s")
        params.append(str(self.backing))

        return params

    def setup(self, timeout: float = None) -> (int, int):
        if not hasattr(self, "_cached_setup"):
            with tempfile.NamedTemporaryFile() as pidfile:
                # HACK: Try up to 10 times to find a port to use. The alternatives
                # would be to let qemu-nbd find a port for us then use netstat to
                # find which one was selected using netstat (or open coding it), or
                # to first pick an empty port ourselves then telling qemu-nbd to
                # use it... but this is inherently racy since we would have to
                # unbind the port before giving it to qemu-nbd and another process
                # may take it in the mean time.
                for i in range(10):
                    port = random.randrange(1025, 65535)
                    r = run(self._qemu_nbd_args(port, pidfile.name), stdout=PIPE, stderr=STDOUT, timeout=timeout)
                    if r.returncode == 0:
                        pid = int(pidfile.read().decode())

                        # NOTE: we acquire a pidfd of the NBD server so that we may refer to it at a later time without
                        # risk of PID reuse
                        self._cached_setup = (port, os.pidfd_open(pid))
                        break

                # We failed multiple times to start
                if not hasattr(self, "_cached_setup"):
                    raise ValueError(f"Exit code {r.returncode}, Output:\n{r.stdout}")

        return self._cached_setup

    @property
    def hostname(self):
        return urlparse(config.EXECUTOR_URL).hostname

    @property
    def tcp_port(self):
        return self.setup()[0]

    @property
    def server_pidfd(self):
        return self.setup()[1]

    def to_b2c_nbd(self, device):
        return f"b2c.nbd={device},host={self.hostname},port={self.tcp_port},connections={self.max_connections}"

    def teardown(self):
        signal.pidfd_send_signal(self.server_pidfd, signal.SIGTERM)

        # Wait for the NBD process to shut down for up to a second, then send a kill signal that cannot be masked
        rfd, _, _ = select.select([self.server_pidfd], [], [], 1)
        if len(rfd) == 0:
            signal.pidfd_send_signal(self.server_pidfd, signal.SIGKILL)
