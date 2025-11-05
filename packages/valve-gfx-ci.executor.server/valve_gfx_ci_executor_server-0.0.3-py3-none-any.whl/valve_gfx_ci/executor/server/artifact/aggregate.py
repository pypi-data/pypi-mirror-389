from functools import cached_property

import os
import hashlib
import tempfile

from .io import ArtifactIOBase


class AggregateArtifact(ArtifactIOBase):
    def __init__(self, artifacts: list[ArtifactIOBase], content_type: str = "application/octet-stream"):
        assert len(artifacts) > 0

        self._artifacts = artifacts
        self._content_type = content_type

        self._pos = 0

    def __artifact_by_offset(self, offset: int) -> ArtifactIOBase:
        for a in self._artifacts:
            artifact_size = a.filesize
            if offset < artifact_size:
                a.seek(offset, os.SEEK_SET)
                return a
            else:
                offset -= artifact_size

        # If we are after every artifact
        return a

    def read(self, size=-1, /) -> bytes:
        rd = b""
        while True:
            f = self.__artifact_by_offset(self._pos)
            buf = f.read(size)
            if len(buf) == 0 and f == self._artifacts[-1]:
                # We have reached the end of the last artifact
                break
            else:
                self._pos += len(buf)
                rd += buf

            # Keep going if we were asked to read all
            if size > -1:
                break

        return rd

    def readall(self) -> bytes:
        return self.read(-1)

    def tell(self):
        return self._pos

    def seek(self, offset, whence=os.SEEK_SET, /):
        if whence == os.SEEK_SET:
            self._pos = offset
        elif whence == os.SEEK_CUR:
            self._pos += offset
        elif whence == os.SEEK_END:
            self._pos = self.filesize + offset
        else:
            raise NotImplementedError()

        return self._pos

    @property
    def content_type(self) -> str:
        return self._content_type

    @cached_property
    def filesize(self) -> int:
        return sum([a.filesize for a in self._artifacts])

    @cached_property
    def _tmp_output_file(self):
        output = tempfile.NamedTemporaryFile()

        # Write all the artifacts to the temporary file
        for artifact in self._artifacts:
            artifact.wait_for_complete()

            # Copy the file
            os.sendfile(output.fileno(), artifact.fileno(), 0, artifact.filesize)

        return output

    def fileno(self):
        if len(self._artifacts) == 1:
            return self._artifacts[0].fileno()

        return self._tmp_output_file.fileno()

    @cached_property
    def filepath(self):
        if len(self._artifacts) == 1:
            return self._artifacts[0].filepath

        return self._tmp_output_file.name

    @property
    def is_complete(self) -> bool:  # pragma: nocover
        return all([a.is_complete for a in self._artifacts])

    @cached_property
    def etag(self) -> str:
        etag = "-".join([a.etag for a in self._artifacts])
        return hashlib.blake2b(etag.encode(), digest_size=16).hexdigest()
