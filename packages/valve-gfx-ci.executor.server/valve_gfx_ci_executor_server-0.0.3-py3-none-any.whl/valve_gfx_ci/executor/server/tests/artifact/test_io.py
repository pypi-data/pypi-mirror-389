from unittest.mock import PropertyMock
from tempfile import mkstemp
from io import FileIO

import os

from server.artifact.io import ArtifactIOBase


class ArtifactIO(FileIO, ArtifactIOBase):
    pass


def create_artifact(tmpdir, data: bytes = b"Hello world!") -> ArtifactIO:
    tmpfilefd, tmpfile_path = mkstemp(dir=tmpdir)
    os.write(tmpfilefd, data)
    os.close(tmpfilefd)

    return ArtifactIO(tmpfile_path)


def test_ArtifactIOBase__filesize(tmpdir):
    data = b"Hello world!"
    artifact = create_artifact(tmpdir, data)

    assert artifact.filesize == 12

    # Make sure the location in the stream does not affect the size
    artifact.seek(10)
    assert artifact.filesize == 12
    assert artifact.tell() == 10


def test_ArtifactIOBase__filepath(tmpdir):
    data = b"Hello world!"
    artifact = create_artifact(tmpdir, data)

    assert open(artifact.filepath, "rb").read() == data


def test_ArtifactIOBase__wait_for_complete(tmpdir):
    artifact = create_artifact(tmpdir)

    # Setup a property mock for the artifact
    is_complete_mock = PropertyMock(side_effect=[False, False, False, True])
    type(artifact).is_complete = is_complete_mock

    assert is_complete_mock.call_count == 0
    artifact.wait_for_complete()
    assert is_complete_mock.call_count == 4


def test_ArtifactIOBase__stream(tmpdir):
    data = b"Hello world!"
    artifact = create_artifact(tmpdir, data)

    assert list(artifact.stream(4, 5)) == [b"Hello", b" worl", b"d!"]
