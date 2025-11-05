from server.artifact.data import DataArtifact

import pytest


def test_DataArtifact__None_raises():
    with pytest.raises(ValueError) as exc:
        DataArtifact(None)

    assert "No data provided" in str(exc)


def test_DataArtifact__unsupported_type_raises():
    with pytest.raises(ValueError) as exc:
        DataArtifact(0)

    assert "Unsupported data type (int)" in str(exc)


def test_DataArtifact__bytes():
    data = b"Hello world"
    artifact = DataArtifact(data)

    assert artifact.content_type == "application/octet-stream"
    assert artifact.filesize == len(data)
    assert artifact.is_complete
    assert artifact.etag == "ff734a0b6c5d9e0f3900c2422d8cc5e1"
    assert artifact.read(3) == b"Hel"
    assert artifact.read() == b"lo world"


def test_DataArtifact__str():
    data = "Hello world"
    artifact = DataArtifact(data)

    assert artifact.content_type == "text/plain;charset=UTF-8"
    assert artifact.etag == "ff734a0b6c5d9e0f3900c2422d8cc5e1"
    assert artifact.read() == data.encode()
