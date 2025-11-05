from io import RawIOBase
from pathlib import Path

import os
import time


class ArtifactIOBase(RawIOBase):
    def readall(self) -> bytes:  # pragma: nocover
        raise NotImplementedError()

    def readinto(self, b, /) -> int:  # pragma: nocover
        raise NotImplementedError()

    def writable(self) -> bool:  # pragma: nocover
        return False

    def writelines(lines, /) -> None:  # pragma: nocover
        raise NotImplementedError()

    def write(self, b, /) -> int:  # pragma: nocover
        raise NotImplementedError()

    @property
    def content_type(self) -> str:  # pragma: nocover
        raise NotImplementedError()

    @property
    def filesize(self) -> int:
        if not self.seekable():
            raise ValueError("The artifact does not provide a filesize nor can be seeked")

        cur_pos = self.tell()
        try:
            return self.seek(0, os.SEEK_END)
        finally:
            self.seek(cur_pos, os.SEEK_SET)

    @property
    def filepath(self):
        return Path("/proc/") / str(os.getpid()) / "fd" / str(self.fileno())

    @property
    def is_complete(self) -> bool:  # pragma: nocover
        raise NotImplementedError()

    def wait_for_complete(self, polling_delay: float = 0.05):
        while not self.is_complete:
            time.sleep(0.05)

    @property
    def etag(self) -> str:  # pragma: nocover
        raise NotImplementedError()

    def stream(self, min_size: int = 1024, max_size: int = 1024**2) -> None:
        """
        Generator to read the whole file

        Parameters
        ----------
        min_size : int
            The minimum size of the chunk to generate
        max_size : int
            The maximum size of the chunk to generate
        """

        assert min_size <= max_size

        while True:
            chunk = b""
            while len(chunk) < min_size:
                chunk_size = int(max_size) - len(chunk)
                rd = self.read(chunk_size)

                # Detect the end of file
                if len(rd) == 0:
                    if len(chunk) > 0:
                        yield chunk
                    return
                else:
                    chunk += rd

            yield chunk
