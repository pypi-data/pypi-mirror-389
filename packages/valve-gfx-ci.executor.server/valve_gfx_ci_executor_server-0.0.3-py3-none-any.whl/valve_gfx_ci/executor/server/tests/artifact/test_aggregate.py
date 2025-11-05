import os

from server.artifact.aggregate import AggregateArtifact
from server.artifact.data import DataArtifact

import hashlib
import pytest


def test_AggregateArtifact__single_artifacts():
    data = b"Wake up, Neo!"
    data_artifact = DataArtifact(data)
    artifact = AggregateArtifact([data_artifact])

    # Check the default content type
    assert artifact.content_type == "application/octet-stream"

    # Reading everything works
    assert artifact.readall() == data

    # Make sure that the returned fileno() is the one from our single artifact
    assert artifact.fileno() == data_artifact.fileno()

    # Make sure the generated filepath is complete
    assert open(artifact.filepath, "rb").read() == data

    # Check the generated ETag
    assert artifact.etag == hashlib.blake2b(data_artifact.etag.encode(), digest_size=16).hexdigest()


def test_AggregateArtifact__multiple_artifacts():
    artifact1 = DataArtifact(b"Hello ")
    artifact2 = DataArtifact("world")
    artifact = AggregateArtifact([artifact1, artifact2],
                                 content_type="ci-tron/custom")

    # Check that we start at position 0
    assert artifact.tell() == 0

    # Ensure the content type is the custom one we set
    assert artifact.content_type == "ci-tron/custom"

    # Reading everything works
    assert artifact.readall() == b"Hello world"
    artifact.seek(0)
    assert artifact.read() == b"Hello world"

    # One read does not span multiple artifacts
    artifact.seek(2)
    assert artifact.read(11) == b"llo "
    assert artifact.read(11) == b"world"

    # Seeking to the end of the artifact works
    artifact.seek(-3, os.SEEK_END)
    assert artifact.tell() == 8
    assert artifact.read() == b"rld"

    # Seeking to a relative offset
    assert artifact.tell() == 11
    assert artifact.seek(-5, os.SEEK_CUR) == 6
    assert artifact.read() == b"world"

    # Unsupported seek type
    with pytest.raises(NotImplementedError):
        artifact.seek(0, os.SEEK_HOLE)

    # Make sure that the returned fileno() is not either of our sub-artifacts'
    assert artifact.fileno() not in [artifact1.fileno(), artifact2.fileno()]

    # Make sure the generated filepath is complete
    assert open(artifact.filepath, "rb").read() == b"Hello world"

    # Check the generated ETag
    assert artifact.etag == hashlib.blake2b(f"{artifact1.etag}-{artifact2.etag}".encode(), digest_size=16).hexdigest()
