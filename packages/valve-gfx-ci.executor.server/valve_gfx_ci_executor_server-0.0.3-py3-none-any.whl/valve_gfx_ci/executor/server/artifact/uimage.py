from enum import StrEnum, auto

import binascii
import struct
import time

from ..dhcpd import CPUArch
from .aggregate import AggregateArtifact
from .data import DataArtifact
from .io import ArtifactIOBase


class UImageFormatCompression(StrEnum):
    NONE = auto()

    @property
    def uboot_id(self):
        if self == UImageFormatCompression.NONE:
            return 0
        else:  # pragma: nocover
            raise ValueError("Unhandled compression format")


class UImageFormatOS(StrEnum):
    LINUX = auto()

    @property
    def uboot_id(self):
        if self == UImageFormatOS.LINUX:
            return 5
        else:  # pragma: nocover
            raise ValueError("Unhandled OS")


class UImageFormatType(StrEnum):
    # Reference: https://github.com/u-boot/u-boot/blob/master/include/image.h
    # WARNING: Define the fields in the same order as image.h!
    INVALID = auto()
    STANDALONE = auto()
    KERNEL = auto()
    RAMDISK = auto()
    MULTI = auto()
    FIRMWARE = auto()
    SCRIPT = auto()
    FILESYSTEM = auto()
    FLATDT = auto()
    KWBIMAGE = auto()
    IMXIMAGE = auto()
    UBLIMAGE = auto()
    OMAPIMAGE = auto()
    AISIMAGE = auto()
    KERNEL_NOLOAD = auto()
    PBLIMAGE = auto()
    MXSIMAGE = auto()
    GPIMAGE = auto()
    ATMELIMAGE = auto()
    SOCFPGAIMAGE = auto()
    X86_SETUP = auto()
    LPC32XXIMAGE = auto()
    LOADABLE = auto()
    RKIMAGE = auto()
    RKSD = auto()
    RKSPI = auto()
    ZYNQIMAGE = auto()
    ZYNQMPIMAGE = auto()
    ZYNQMPBIF = auto()
    FPGA = auto()
    VYBRIDIMAGE = auto()
    TEE = auto()
    FIRMWARE_IVT = auto()
    PMMC = auto()
    STM32IMAGE = auto()
    SOCFPGAIMAGE_V1 = auto()
    MTKIMAGE = auto()
    IMX8MIMAGE = auto()
    IMX8IMAGE = auto()
    COPRO = auto()
    SUNXI_EGON = auto()
    SUNXI_TOC0 = auto()
    FDT_LEGACY = auto()
    RENESAS_SPKG = auto()
    STARFIVE_SPL = auto()
    TFA_BL31 = auto()

    @property
    def uboot_id(self):
        for i, value in enumerate(UImageFormatType):
            if self == value:
                return i


class UImageArtifact(AggregateArtifact):
    def __init__(self, artifact: ArtifactIOBase, architecture: CPUArch, compression: UImageFormatCompression,
                 os: UImageFormatOS, type: UImageFormatType):
        # Generate the crc32 of the artifact
        size_hdr = struct.pack(">II", artifact.filesize, 0)
        dcrc = binascii.crc32(size_hdr)
        for chunk in artifact.stream():
            dcrc = binascii.crc32(chunk, dcrc)

        MAGIC = 0x27051956
        hdr = struct.pack(">7I4b32x",
                          MAGIC, 0, int(time.time()), len(size_hdr) + artifact.filesize, 0, 0, dcrc,
                          os.uboot_id, architecture.uboot_arch_id,
                          type.uboot_id, compression.uboot_id)
        hcrc = binascii.crc32(hdr)
        header = DataArtifact(hdr[0:4] + struct.pack(">I", hcrc) + hdr[8:] + size_hdr)

        super().__init__([header, artifact], content_type="application/x.uimage")
