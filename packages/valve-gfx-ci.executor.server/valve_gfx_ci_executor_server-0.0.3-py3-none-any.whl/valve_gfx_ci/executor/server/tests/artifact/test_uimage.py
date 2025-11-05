from datetime import datetime
from freezegun import freeze_time

from server.artifact.uimage import UImageFormatCompression, UImageFormatOS, UImageFormatType, UImageArtifact
from server.artifact.data import DataArtifact

from server.dhcpd import CPUArch


def test_UImageFormatCompression():
    # Make sure that every enum value has an associated id
    for f in UImageFormatCompression:
        f.uboot_id

    # Check the IDs
    assert UImageFormatCompression.NONE.uboot_id == 0


def test_UImageFormatOS():
    # Make sure that every enum value has an associated id
    for f in UImageFormatOS:
        f.uboot_id

    # Check the IDs
    assert UImageFormatOS.LINUX.uboot_id == 5


def test_UImageFormatType():
    # Make sure that every enum value has an associated id
    for f in UImageFormatType:
        f.uboot_id

    # Check the IDs
    assert UImageFormatType.SCRIPT.uboot_id == 6


def test_UImageArtifact():
    start_time = datetime(2024, 9, 23, 12, 0, 0)
    with freeze_time(start_time.isoformat()):
        f = UImageArtifact(DataArtifact(b"Hello world"), architecture=CPUArch.X86_64,
                           compression=UImageFormatCompression.NONE, os=UImageFormatOS.LINUX,
                           type=UImageFormatType.SCRIPT)

        assert f.etag == "81cd372c6ddc0973b544144b075d9786"
