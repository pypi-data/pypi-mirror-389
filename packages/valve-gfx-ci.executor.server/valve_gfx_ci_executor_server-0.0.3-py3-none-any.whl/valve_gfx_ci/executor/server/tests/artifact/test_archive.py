from pathlib import Path
import tempfile
import tarfile
import re
import zipfile

import pytest

from server.artifact.archive import (ArtifactAdd, ArtifactKeep, ArchiveArtifact, ArchiveFormat, ArchiveCompression,
                                     EntryNotFound)
from server.artifact.data import DataArtifact


def test_ArtifactKeep__matches():
    def match_keep(path_re, path, rewrite=None):
        return ArtifactKeep(path=re.compile(path_re), rewrite=rewrite).matches(path)

    assert match_keep("/helloworld", "/helloworld") == "/helloworld"
    assert match_keep("/(helloworld)", "/helloworld", rewrite=r"/boot/\1") == "/boot/helloworld"
    assert match_keep("/helloworld", "/other") is None


def create_mock_archive(f):
    f.wait_for_complete = lambda: None

    # Create an archive
    with tempfile.TemporaryDirectory() as ad:
        say = Path(ad) / "say"
        say.mkdir()
        (say / "greetings").write_bytes(b"Hello World")
        (say / "goodbye").write_bytes(b"Bye bye")
        (say / "symlink").symlink_to("greetings")

        src = tarfile.open(mode='w:gz', fileobj=f)
        src.add(say, "say")
        src.close()

    # Rewind the file
    f.seek(0)


def test_ArchiveArtifact__no_entry_found():
    with tempfile.TemporaryFile(mode='w+b') as f:
        create_mock_archive(f)

        with pytest.raises(EntryNotFound) as exc:
            ArchiveArtifact(f, format=ArchiveFormat.NONE, compression=ArchiveCompression.NONE,
                            keep=[ArtifactKeep(re.compile("^missing$"))])

        assert "Couldn't find a matching entry" in str(exc)


def test_ArchiveArtifact__symlink_as_artifact():
    with tempfile.TemporaryFile(mode='w+b') as f:
        create_mock_archive(f)

        with pytest.raises(EntryNotFound) as exc:
            ArchiveArtifact(f, format=ArchiveFormat.NONE, compression=ArchiveCompression.NONE,
                            keep=[ArtifactKeep(re.compile("^say/symlink$"))])

        assert "Cannot use a symlink as an artifact" in str(exc)


def test_ArchiveArtifact__targz_to_none():
    with tempfile.TemporaryFile(mode='w+b') as f:
        create_mock_archive(f)

        artifact = ArchiveArtifact(f, format=ArchiveFormat.NONE, compression=ArchiveCompression.NONE,
                                   keep=[ArtifactKeep(re.compile("^say/greetings$"))])

        assert artifact.read() == b"Hello World"


def test_ArchiveArtifact__targz_to_zip():
    with tempfile.TemporaryFile(mode='w+b') as f:
        create_mock_archive(f)

        # Create a zip archive from it, adding an extra file for testing
        artifact = ArchiveArtifact(f, format=ArchiveFormat.ZIP, compression=ArchiveCompression.NONE,
                                   keep=[ArtifactKeep(re.compile("^(say/|say/(greetings|symlink))$"),
                                                      rewrite=r"/opt/\1")],
                                   add=[ArtifactAdd(artifact=DataArtifact(b'Bye bye'), path="/opt/say/goodbye")])

        assert artifact.content_type == "application/octet-stream"
        assert artifact.is_complete
        assert artifact.etag

        # Open the resulting archive to verify the content list and data
        with zipfile.ZipFile(artifact, mode="r") as zf:
            assert zf.namelist() == ['/opt/', '/opt/say/', '/opt/say/greetings', '/opt/say/symlink', '/opt/say/goodbye']

            with zf.open("/opt/say/greetings") as zf_greetings:
                assert zf_greetings.read() == b"Hello World"

            with zf.open("/opt/say/goodbye") as zf_goodbye:
                assert zf_goodbye.read() == b"Bye bye"


def test_ArchiveArtifact__no_source_archive_but_keeps_specified():
    with pytest.raises(ValueError) as exc:
        ArchiveArtifact(None, format=ArchiveFormat.CPIO, compression=ArchiveCompression.NONE,
                        keep=[ArtifactKeep(re.compile("^missing$"))])

    assert "Can't keep artifacts if no source archive is provided" in str(exc)


def test_ArchiveArtifact__adding_files_to_None_archive():
    with pytest.raises(ValueError) as exc:
        ArchiveArtifact(None, format=ArchiveFormat.NONE, compression=ArchiveCompression.NONE,
                        add=[ArtifactAdd(artifact=None, path="/file")])

    assert "Can't add files to a NONE-format archive" in str(exc)
