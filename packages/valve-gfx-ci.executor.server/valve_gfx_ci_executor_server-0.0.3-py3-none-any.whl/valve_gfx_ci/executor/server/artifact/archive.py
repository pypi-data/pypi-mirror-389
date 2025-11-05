from dataclasses import dataclass
from enum import StrEnum, auto
from io import FileIO
from pathlib import PurePath

import hashlib
import os
import re
import sys
import time
import traceback

from libarchive import Archive, Entry, _libarchive
from .io import ArtifactIOBase


class ArchiveFormat(StrEnum):
    NONE = auto()
    CPIO = auto()
    ISO = auto()
    TAR = auto()
    ZIP = auto()


class ArchiveCompression(StrEnum):
    NONE = auto()
    GZ = auto()
    BZ2 = auto()


@dataclass
class ArtifactKeep:
    path: re.Pattern
    rewrite: str | None = None

    def matches(self, path) -> str:
        if self.path.fullmatch(path):
            if self.rewrite:
                return self.path.sub(self.rewrite, path)
            else:
                return path


@dataclass
class ArtifactAdd:
    artifact: ArtifactIOBase

    path: str
    mode: int = 0o100644
    size: int = None
    mtime: float = None

    def to_entry(self):
        size = self.size if self.size else self.artifact.filesize
        mtime = self.mtime if self.mtime else time.time()
        return Entry(pathname=self.path, mode=self.mode, size=size, mtime=mtime)


class EntryNotFound(ValueError):
    pass


class ArchiveArtifact(FileIO, ArtifactIOBase):
    def __stream_entry(self, entry, read_fn, write_fn):
        if entry.symlink == '':
            for chunk in read_fn:
                write_fn(chunk)
                self._etag.update(chunk)

    def __add_file(self, output_archive, entry, read_fn, write_fn):
        # Make sure all the parent folders exist, going from the root to the leaf
        for parent in reversed(PurePath(entry.pathname).parents):
            parent = str(parent)
            if parent not in self.written_dir_entries:
                parent_entry = Entry(pathname=parent, size=0, mtime=entry.mtime, mode=0o40755)
                parent_entry.to_archive(output_archive)
                self.written_dir_entries[parent_entry.pathname] = parent_entry

        # Keep track of all the folders we have written out
        if entry.isdir():
            self.written_dir_entries[entry.pathname.removesuffix("/")] = entry

        # Add the file to the new archive
        entry.to_archive(output_archive)
        self.__stream_entry(entry, read_fn, write_fn)
        _libarchive.archive_write_finish_entry(output_archive._a)

    def __init__(self, artifact: ArtifactIOBase, format: ArchiveFormat, compression: ArchiveCompression,
                 keep: list[ArtifactKeep] = [], add: list[ArtifactAdd] = []):
        self.written_dir_entries = {".": None, "/": None}
        self._etag = hashlib.blake2b(digest_size=16)

        def find_match(pathname: str) -> str:
            for match in keep:
                if rewritten_path := match.matches(pathname):
                    return match, rewritten_path

            return None, None

        if len(keep) > 0 and artifact is None:
            raise ValueError("Can't keep artifacts if no source archive is provided")
        elif format == ArchiveFormat.NONE and len(add) > 0:
            raise ValueError("Can't add files to a NONE-format archive")

        memfd = FileIO(os.memfd_create("ArchiveArtifact"), "wb", closefd=False)
        if format != ArchiveFormat.NONE:
            filter = compression.value if compression and compression != ArchiveCompression.NONE else None
            output_archive = Archive(memfd, "w", format=format.value, filter=filter)
            def archive_write_fn(data): _libarchive.archive_write_data_from_str(output_archive._a, data)
        else:
            output_archive = None

        try:
            # Keep all the wanted files from the source archive, if asked to
            if artifact:
                # Wait for the artifact to be done downloading since libarchive won't
                # call the emulated read function and thus requires all the data to be
                # present before parsing
                artifact.wait_for_complete()

                with Archive(artifact, "r") as a:
                    # Find a matching file in the archive
                    is_empty = True
                    for entry in a:
                        # Try to find a match for the entry
                        _, rewritten_path = find_match(entry.pathname)
                        if rewritten_path:
                            is_empty = False
                            if output_archive:
                                entry.pathname = rewritten_path
                                self.__add_file(output_archive, entry, a.readstream(entry.size), archive_write_fn)
                            else:
                                if entry.symlink:
                                    raise EntryNotFound("Cannot use a symlink as an artifact")

                                # Just stream the artifact directly to the memfd, then stop looking for a match
                                self.__stream_entry(entry, a.readstream(entry.size), memfd.write)
                                break

                    if is_empty:
                        raise EntryNotFound("Couldn't find a matching entry")

            # Add all the new entries wanted
            if output_archive:
                for a_add in add:
                    self.__add_file(output_archive, a_add.to_entry(), a_add.artifact.stream(), archive_write_fn)

            # Finish writing the archive, then reset the file
            if output_archive:
                output_archive.close()
            memfd.flush()
            memfd.seek(0)
            super().__init__(memfd.fileno(), mode='r', closefd=True)
        except Exception as e:
            if not isinstance(e, EntryNotFound):  # pragma: nocover
                traceback.print_exc(file=sys.stderr)
            memfd.close()
            raise e from None

    @property
    def content_type(self) -> str:
        return "application/octet-stream"

    @property
    def is_complete(self) -> bool:
        return True

    @property
    def etag(self) -> str:
        return self._etag.hexdigest()
