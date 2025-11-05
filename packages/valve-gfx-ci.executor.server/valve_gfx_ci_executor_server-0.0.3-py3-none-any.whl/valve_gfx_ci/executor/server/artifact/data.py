from io import FileIO

import os
import hashlib

from .io import ArtifactIOBase


class DataArtifact(FileIO, ArtifactIOBase):
    def __init__(self, data: bytes | str = b""):
        """
        Create an artifact that contains the data provided as a parameter. This
        is roughly equivalent to using BytesIO, but with full compatibility
        with the HTTP artifacts: ability to stream content, content type, ETag,
        and so on...

        Parameters
        ----------
        data : bytes | str
            The data you want to expose as an artifact
        """

        if data is None:
            raise ValueError("No data provided")

        if type(data) is str:
            data = data.encode()
            content_type = "text/plain;charset=UTF-8"
        elif type(data) is bytes:
            content_type = "application/octet-stream"
        else:
            raise ValueError(f"Unsupported data type ({type(data).__name__})")

        self._content_type = content_type
        self._etag = hashlib.blake2b(data, digest_size=16).hexdigest()

        # Create an anonymous file, so that it can be referenced by external tools or C code
        memfd = os.memfd_create("DataArtifact")
        os.write(memfd, data)
        os.lseek(memfd, 0, os.SEEK_SET)

        super().__init__(memfd, mode='r', closefd=True)

    @property
    def content_type(self) -> str:
        return self._content_type

    @property
    def is_complete(self) -> bool:
        return True

    @property
    def etag(self) -> str:
        return self._etag
