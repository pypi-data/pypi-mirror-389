from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timedelta, UTC
from enum import Enum, Flag, auto
from functools import cached_property
from hashlib import blake2b
from io import IOBase, FileIO
from pathlib import Path
from threading import Thread, Event, Lock, RLock
import email.utils
import fcntl
import json
import os
import shutil
import time
import traceback
import re

from pydantic.dataclasses import dataclass
from pydantic import HttpUrl, field_validator, DirectoryPath

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests

from .io import ArtifactIOBase

"""
Introduction
------------

We decided to create our own artifact cache because the existing ones were
not providing the right interfaces and capabilities to address our needs. We
thus set out to design a data structure and interface that would meet the
following requirements:

1. Ressource efficient:
     Minimize the network bandwidth, along with RAM and CPU usage
2. Reliable:
     The cache should be resistent to network/download failures and
     automatically restart when possible.
3. Low-latency:
     Access to the artifact should be streamable from cache or from the
     internet transparently, without the need to first wait for the download
     to finish.
4. Multi-process:
     Should use the minimal amount of synchronisation to make parallel access
     to the cache from multiple thread or processes as fast as possible. Cache
     requests for the same URL coming from multiple processes should be
     de-duplicated and only result in one download
5. Simple to use:
   Provide the methods needed to either open the artifact as a file-like even
   during artifact download, or get a filepath when the download is finished,
   without having to think about locking or being optimal.

Overall solution
----------------

The crux of the solution is the use of a file that is opened multiple times for
different purpose, and the use of multiple UNIX locks. Principles of operation:

 * Write the data as fast as it downloaded so that other readers are not
   throttled by the reading speed of the first requester
 * Linux extended attributes are used to signal whether the file is complete,
   or stale (the file on the server changed during the download and thus cannot
   be completed)
 * UNIX file locks are used to keep the cache coherent, make sure only one
   writer is writing data to the file, and allow readers to know if a writer is
   currently active by trying to acquire a shared lock on the body.
 * Readers can stream the content while it is downloaded by simply calling
  `$file.read()`. Once they reach the end of the file, the reader can wait if
  the completion time xattr isn't set on the body, return if it was, assert if
  the body is marked as STALE, or resume the download if the writer thread died.
 * Multiple readers can refer to the same version of the file by opening
   `/proc/$pid/fd/$fileno` even if the file has been overwritten by a newer
   version. It only requires the writer to delete the file before creating a new
   version.

The cache is split into 5 main classes:

  * HttpArtifact:
      Responsible for HTTP requests and acquiring instances of the artifact

  * CachedResponse:
      Represents the artifact view from the server's perspective... AKA the HTTP
      response. It handles serializing/deserializing, parsing, and tagging to
      indicate if the ressource is still fresh, needs revalidation, ...
      See https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching for an
      overview of the HTTP caching mechanisms.

  * HttpArtifactInstance:
      Responsible for holding open a file containing the artifact wanted by the
      user, and provide methods to open the file or return its path on disk...
      after automatically waiting for the download to be over for ease of use.

  * HttpArtifactIO:
     Returned by HttpArtifactInstance.open(), it allows accessing the content of
     the artifact as a file-like, even while the file is being downloaded.

  * HttpArtifactWriter:
      Responsible for asynchronously writing the content of the artifact to a
      file on disk, resuming downloads automatically if the network crashed,
      and making sure the artifact did not change on the server side when
      resuming.

On disk, the cache structure is the following:

    $root / url_hash[0:2] / url_hash[2:4] / url_hash[4:]:
      - response.json: Contains the latest response from the http server
      - body         : Contains the current body

Multiprocessing model
---------------------

To keep both the `response.json` and `body` file in sync with each-other,
processes accessing the cache first need to acquire an exclusive lock on the
url cache directory.

The lock is kept until the body has been validated to be up to date, and an
HttpArtifactInstance object has been created to link to the current body and keep
the reference alive even if a future request requires a re-download of the
body. Validation of the body can be done using one of the following methods:

 * IN_FLIGHT_REUSE: The artifact was already being downloaded, so was fresh-enough
 * FRESH_CACHE_REUSE: The cached artifact was still fresh
 * REUSE_AFTER_REVALIDATION: The cached artifact was re-used after revalidation
 * FULL_DOWNLOAD: The artifact was downloaded and cached

If a FULL_DOWNLOAD is needed or if the current body can be re-used but is
incomplete, a HttpArtifactWriter instance is created. This instance will acquire an
exclusive lock on the body file. This lock enforces that only one process may
download the file at a time... while also allowing others to check if a process
currently holds the lock by attempting to lock the body using a shared lock.
A shared lock is used to check if there is a body writer since multiple readers
may acquire this lock and the only reason for it to fail is for another process
to hold an exclusive lock.

If an HttpArtifactInstance object reaches the end of the artifact, no STALE or
COMPLETION_TIME extended attribute are found, and no writer is currently active,
it will start a new HttpArtifactWriter to finish the download. The writer will be
supplied with the cached response so that it can ensure that the body it resumes
downloading is the same one it started with.
"""

# All these attributes should store bytes representing a single float
XATTR_START_TIME = b"user.artifactcache.start_time"
XATTR_COMPLETION_TIME = b"user.artifactcache.completion_time"
XATTR_RESUME_CNT = b"user.artifactcache.resume_cnt"
XATTR_STALE = b"user.artifactcache.stale"

# Size of the block used when writing to disk the artifact being downloaded. It
# should be a tradeof between writing data to disk early to make it available
# to readers as fast as possible, and efficiency by not writing too few bytes
# which would needlessly increase the CPU overhead.
#
# NOTE: Try to use a multiple of the system's page size to give the kernel a
# chance to write the block down atomatically and in a zero-copy fashion
WRITE_BLOCK_SIZE = 16384

# Function signature for the callback function
LogCallback = Callable[[str], None]


class CacheState(Flag):
    """Represents the state of a CachedResponse"""

    NO_TAGS = 0                       # The artifact has no field that would help

    # Uncachability (these should probably be deleted first)
    UNCACHEABLE_STATUS_CODE = auto()  # The artifact was returned using an uncacheable status code
    NO_STORE = auto()                 # The artifact was tagged as no-store by the server

    # Attributes
    HAS_EXPIRATION = auto()           # The artifact has an expiration date
    HAS_LAST_MODIFIED = auto()        # The artifact has a Last-Modified field
    HAS_ETAG = auto()                 # The artifact has an ETag
    ACCEPTS_RANGES = auto()           # The artifact can be downloaded in parts
    IMMUTABLE = auto()                # The artifact was tagged as immutable by the server

    # Freshness
    NO_CACHE = auto()                 # The artifact was tagged as no-cache by the server
    FRESH = auto()                    # The artifact can be re-used without prior revalidation

    # Reusability after staleness
    REUSE_WHILE_REVALIDATE = auto()   # The cached artifact may be re-used but background revalidation needed
    REUSE_ON_ERROR = auto()           # The cached artifact may be re-used if an error occured during revalidation

    @property
    def is_reusable(self):
        # The cached artifact may be re-used in some conditions
        return self.UNCACHEABLE_STATUS_CODE not in self and self.NO_STORE not in self

    @property
    def can_revalidate(self):
        # The cached artifact has the information needed to get it revalidated
        return self.is_reusable and (self.HAS_ETAG in self or self.HAS_LAST_MODIFIED in self)

    @property
    def is_fresh(self):
        return self.is_reusable and self.FRESH in self


@dataclass
class CachedResponse:
    """
    Represents the artifact view from the server's perspective... AKA the HTTP
    response. It handles serializing/deserializing, parsing, and tagging to
    indicate if the resource is still fresh, needs revalidation, ...
    See https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching for an
    overview of the HTTP caching mechanisms.
    """

    url: str
    status_code: int
    headers: dict[str, str]

    # Don't trust the server time?
    created_at: str | None = None

    def __post_init__(self):
        # Store the local time at which this CachedResponse was created, so
        # that it can be correlated with the server's time
        if self.created_at is None:
            self.created_at = email.utils.format_datetime(self.now)

    def serialize(self) -> str:
        return json.dumps(asdict(self))

    @field_validator("headers")
    @classmethod
    def lower_headers(cls, headers: dict[str, str]):
        return {k.lower(): v for k, v in headers.items()}

    def get(self, key: str, default: str = None) -> str:
        return self.headers.get(key.lower(), default)

    def get_date(self, key: str, default: datetime = None) -> datetime:
        if date := self.get(key):
            return self.parse_date(date)
        else:
            return default

    @property
    def content_type(self) -> str:
        return self.get("Content-Type", "application/octet-stream")

    @property
    def content_length(self) -> int:
        if length := self.get("Content-Length"):
            return int(length)

    @property
    def now(self) -> datetime:
        return datetime.now(UTC)

    @property
    def age(self) -> timedelta:
        return self.now - self.parse_date(self.created_at)

    @property
    def client_date(self) -> datetime:
        return self.parse_date(self.created_at)

    @property
    def server_date(self) -> datetime:
        # Use the server date when possible, or fallback to the client's creation date
        return self.get_date("Date", self.client_date)

    @property
    def cache_control(self) -> dict[str, timedelta | None]:
        cache_control = dict()
        for param in [f.strip() for f in self.get("cache-control", "").split(",")]:
            if len(param) == 0:
                continue

            fields = param.split('=')
            if len(fields) == 2:
                cache_control[fields[0]] = timedelta(seconds=int(fields[1]))
            else:
                cache_control[param] = None

        return cache_control

    @property
    def accept_ranges(self) -> str | None:
        unit = self.get("Accept-Ranges", "").lower()
        if unit in ["bytes"]:
            return unit

    @classmethod
    def is_cacheable_status_code(cls, status_code):
        # Source: https://developer.mozilla.org/en-US/docs/Glossary/Cacheable
        return status_code in [
            200,   # OK
            203,   # Non-Authoritative Information
            204,   # No Content
            206,   # Partial Content
            300,   # Multiple Choices
            301,   # Moved Permanently
            308,   # Permanent Redirect
            # 404, # Not Found     --> Disabled since the condition may be temporary
            405,   # Method Not Allowed
            410,   # Gone
            414,   # URI Too Long
        ]

    @property
    def tags(self) -> CacheState:
        cache_control = self.cache_control

        tags = CacheState.NO_TAGS

        if not self.is_cacheable_status_code(self.status_code):
            tags |= CacheState.UNCACHEABLE_STATUS_CODE

        # Are we asked not to store the artifact? Pay attention that `no-store` should
        # be ignored if `must-understand` is present.
        # See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#must-understand
        if ("no-store" in cache_control and "must-understand" not in cache_control):
            tags |= CacheState.NO_STORE

        # NOTE: no-cache has been handled differently throughout the history of HTTP,
        # without actual differences in expected behaviour from the client. So let's
        # map all conditions to same tag
        if "no-cache" in cache_control or "must-revalidate" in cache_control or self.get("Pragma") == "no-cache":
            tags |= CacheState.NO_CACHE

        # Find the earliest expiration age, giving priority to Cache-Control over Expires and heuristic caching
        earliest_expiration_age = timedelta.max
        max_age = cache_control.get("max-age")
        if max_age is not None:  # NOTE: Can be 0, so compare to None to check for existence
            earliest_expiration_age = min(earliest_expiration_age, max_age)
        if expires := self.get_date("expires"):  # HTTP/1.0
            # Ensure both the server and expires dates are "aware" by converting them to the local timezone before
            # substracting them to get the expiration age
            earliest_expiration_age = min(earliest_expiration_age, expires.astimezone() - self.server_date.astimezone())
        if last_modified := self.get_date("Last-Modified"):
            tags |= CacheState.HAS_LAST_MODIFIED

            # If no other expiration method was found, check for heuristic caching
            # See https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching#heuristic_caching
            if earliest_expiration_age == timedelta.max:
                earliest_expiration_age = min(earliest_expiration_age, (self.server_date - last_modified) * 0.1)

        # Set the expiration-related tags
        if earliest_expiration_age < timedelta.max:
            tags |= CacheState.HAS_EXPIRATION
            if self.age < earliest_expiration_age:
                tags |= CacheState.FRESH

        # Let the controller know if it can re-use the cache while revalidating or if revalidation failed
        if CacheState.FRESH not in tags:
            if reval_delta := cache_control.get('stale-while-revalidate'):  # NOTE: if 0, no need to check
                if self.now < self.client_date + earliest_expiration_age + reval_delta:
                    tags |= CacheState.REUSE_WHILE_REVALIDATE
            if reval_delta := cache_control.get('stale-if-error'):  # NOTE: if 0, no need to check
                if self.now < self.client_date + earliest_expiration_age + reval_delta:
                    tags |= CacheState.REUSE_ON_ERROR

        # NOTE: We ignore VARY here since we do not allow setting any headers when making an artifact request

        # Misc flags

        if self.get("ETag"):
            tags |= CacheState.HAS_ETAG

        if "immutable" in cache_control:
            tags |= CacheState.IMMUTABLE

        if self.accept_ranges:
            tags |= CacheState.ACCEPTS_RANGES

        return tags

    def revalidatation_headers(self) -> dict[str, str]:
        """Return the http headers to use to tell the server what file we currently have"""

        headers = dict()

        if etag := self.get("ETag"):
            headers["If-None-Match"] = etag

        if last_modified := self.get("Last-Modified"):
            headers["If-Modified-Since"] = last_modified

        return headers

    def update(self, response: requests.Response) -> None:
        new_headers = self.lower_headers(response.headers)

        created_at = email.utils.format_datetime(self.now)
        if response.status_code == 304:
            # Successful revalidation: Update the cache with the updated fields
            # TODO: limit the headers that we can update (?)
            self.headers.update(new_headers)
            self.created_at = created_at
        elif self.is_cacheable_status_code(response.status_code):
            # We got entirely new headers,=
            self.status_code = response.status_code
            self.headers = new_headers
            self.created_at = created_at
        else:
            # NOTE: Don't overwrite our cache with uncacheable artifacts since we may be able to reuse the current one
            pass

    def save(self, path: Path) -> None:
        with open(path, "w") as f:
            f.write(self.serialize())

    def __str__(self) -> str:
        return f"<CachedResponse {self.tags.name}>"

    @classmethod
    def parse_date(cls, date: str) -> datetime:
        return email.utils.parsedate_to_datetime(date)

    @classmethod
    def from_file(cls, path: Path) -> "CachedResponse":
        try:
            with open(path) as f:
                return cls(**json.load(f))
        except Exception:  # pragma: nocover
            # Consider any error as if the cached entry did not exist
            pass

    @classmethod
    def from_request_response(cls, r: requests.Response) -> "CachedResponse":
        # NOTE: In the presence of redirections, the final URL will be
        # different from the one we originally asked for... so let's just keep
        # the one we asked for.
        url = r.history[0].url if len(r.history) > 0 else r.url

        return cls(url=url, status_code=r.status_code, headers=r.headers)


class HttpArtifactWriter(Thread):
    """
    Responsible for asynchronously writing the content of the artifact to a
    file on disk, resuming downloads automatically if the network crashed, and
    making sure the artifact did not change on the server side when resuming
    """

    def __init__(self, artifact: "HttpArtifact", cached_response: CachedResponse,
                 body_path: Path, name: str = "<unnamed>", request: requests.Response = None):
        """
        Download or resume downloading an artifact's body

        Parameters
        ----------
        artifact : HttpArtifact
            The artifact this writer is for
        cached_response : CachedResponse
            The CachedResponse this body is for
        body_path: Path
            The path to the artifact
        name: str
            The name of the artifact, so that it can be used in log messages
        request : requests.Response
            The requests' response that should be used to download the artifact
            or None if wanting to resume downloading an existing body
        """

        super().__init__(name=f'HttpArtifactWriter-{name}')

        self.artifact = artifact
        self.cached_response = cached_response
        self.body_path = Path(body_path)
        self.name = name
        self.request = request

        # We need to create a new body so that the current request and all subsequent ones
        # start using this new body, but also make sure we do not accidentally affect existing
        # processes that may be already reading the current body. This is achieved by simply
        # removing/unlinking the current body before creating a new one
        if request:
            # Ensure the artifact is locked while we create a new body
            assert self.artifact._is_locked, "Tried to create a new body without holding the artifact lock!"

            # We have the lock, so no need to care about atomicity
            if self.body_path.exists():
                self.body_path.unlink()

        # Open the file in write mode without truncation
        write_fd = os.open(self.body_path, os.O_CREAT | os.O_WRONLY, mode=0o666)
        self.writer = os.fdopen(write_fd)

        # Lock the body file so that body readers may know we have someone taking care of downloading the body
        fcntl.flock(self.writer.fileno(), fcntl.LOCK_EX)

        # Abort early if the body is already marked as stale or complete
        if self.get_xattr_as_float(self.writer.fileno(), XATTR_COMPLETION_TIME) or \
           self.get_xattr_as_float(self.writer.fileno(), XATTR_STALE):
            return

        # Write the DL start time, if missing!
        if not self.get_xattr_as_float(self.writer.fileno(), XATTR_START_TIME):
            os.setxattr(self.writer.fileno(), XATTR_START_TIME, str(time.time()).encode())

        self.start()

    @classmethod
    def _gen_resume_headers(cls, cur_loc: int, cached_response: CachedResponse):
        headers = {}

        # Try restarting from where we were if possible
        cache_tags = cached_response.tags
        if cur_loc > 0 and CacheState.ACCEPTS_RANGES in cache_tags:
            # Try to get the content of the artifact, starting from the position if possible
            headers["Range"] = f"bytes={cur_loc}-"

            last_modified = cached_response.get("Last-Modified")
            if last_modified:
                headers["If-Unmodified-Since"] = last_modified

            etag = cached_response.get("ETag")
            if etag:
                headers["If-Range"] = etag
            elif last_modified:
                headers["If-Range"] = last_modified

        return headers

    @classmethod
    def _validate_resume_response(cls, name: str, writer: IOBase, cached_response: CachedResponse,
                                  request_response: requests.Response):
        cur_loc = writer.tell()

        ncr = CachedResponse.from_request_response(request_response)

        non_matching_fields = [f for f in ["Etag", "Last-Modified"] if ncr.get(f) != cached_response.get(f)]
        if len(non_matching_fields) == 0:
            # We ensured that the artifact did not change behind our back, to
            # the extent the server allowed us to, now let's see if we need to
            # redownload the whole thing or can continue from where we were

            if request_response.status_code == 206:
                # The partial range was accepted, continue where we left off!
                if returned_range := ncr.get("Content-Range"):
                    assert re.match(f'bytes[ =]{cur_loc}-', returned_range), \
                            f"[{name}] Unexpected range result. Asked for 'bytes={cur_loc}-', got '{returned_range}'"

                    return request_response
                else:
                    raise ValueError(f"[{name}] Content-Range is missing from the headers despite a 206 status code")
            elif request_response.status_code == 200:
                # Our partial range request was denied or was unsupported, so start again from the top!
                writer.seek(0, os.SEEK_SET)
                return request_response
            else:
                # The file doesn't seem to be available anymore, mark the artifact as stale!
                os.setxattr(writer.fileno(), XATTR_STALE, b"1")

                raise ValueError(f"[{name}] Unexpected status code: {request_response.status_code}")
        else:
            # The file has changed since we started using, so mark the body as stale then exit
            os.setxattr(writer.fileno(), XATTR_STALE, b"1")

            msg = f"[{name}] The file changed and requires a full redownload. Changed fields: {non_matching_fields}"
            raise ValueError(msg)

    def resume_download(self):
        """
        Resume the download from where we left off, making sure that the file
        has not changed on the server side in the mean time
        """

        # Go to the end of the file, where we will be appending new data, then check the current location
        self.writer.seek(0, os.SEEK_END)
        cur_loc = self.writer.tell()

        # Try restarting from where we were if possible
        headers = self._gen_resume_headers(cur_loc, self.cached_response)
        headers_str = ", ".join(headers.keys())
        msg = f"[{self.name}] Resuming download at {cur_loc} bytes using the following headers: {headers_str}"
        self.artifact.log_callback(msg)

        # Bump the resume count
        resume_cnt = round(self.get_xattr_as_float(self.writer.fileno(), XATTR_RESUME_CNT, default=0.0))
        os.setxattr(self.writer.fileno(), XATTR_RESUME_CNT, str(resume_cnt + 1).encode())

        # Make the query
        r = self.artifact._do_get(url=self.cached_response.url, headers=headers)

        # Validate that the response is valid, and setup the writer
        return self._validate_resume_response(name=self.name, writer=self.writer, cached_response=self.cached_response,
                                              request_response=r)

    def run(self):
        """
        This thread will download and store data as fast as possible, and
        handle retries on network issues
        """

        try:
            while True:
                if self.request is None:
                    # We do not have an existing request we can use to keep downloading
                    self.request = self.resume_download()

                try:
                    # Write to disk the data coming from the request as soon as it is available
                    for chunk in self.request.iter_content(WRITE_BLOCK_SIZE):
                        os.write(self.writer.fileno(), chunk)
                except requests.exceptions.StreamConsumedError:
                    # We are done downloading the file! Mark the body as complete before closing the writer
                    os.setxattr(self.writer.fileno(), XATTR_COMPLETION_TIME, str(time.time()).encode())
                    return
                except Exception:
                    self.artifact.log_callback(traceback.format_exc())
                    self.request = None
        finally:
            self.writer.close()
            self.writer = None

    @classmethod
    def has_active_writer(cls, path: Path) -> bool:
        """
        Try acquiring a shared (read-only) lock, which would fail immediately
        if an active writer kept his exclusive lock open.
        """

        try:
            with open(path) as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)

                    # NOTE: The lock will be released automatically when the file gets closed after exciting `with:`
                    return False
                except OSError:
                    return True
        except Exception:
            return False

    @classmethod
    def get_xattr_as_float(cls, path: Path | int, attr: bytes, default: float = 0.0) -> float:
        """
        Returns the extended attribute from the specified path, parsed as a
        float. If the attribute is missing, the provided default is returned
        instead.
        """

        try:
            value = os.getxattr(path, attr)
            return float(value.decode())
        except OSError:
            return default


class HttpFetchingMethod(Enum):
    """Describe how an artifact was fetched, so that users may display useful log messages"""

    IN_FLIGHT_REUSE = "The artifact was already being downloaded, so was fresh-enough"
    FRESH_CACHE_REUSE = "The cached artifact was still fresh"
    REUSE_AFTER_REVALIDATION = "The cached artifact was re-used after revalidation"
    REUSE_DUE_TO_ERROR = "The cached artifact was re-used due to hitting an error"
    FULL_DOWNLOAD = "The artifact was downloaded and cached"


class StaleHttpArtifactException(ValueError):
    pass


class HttpArtifactIO(FileIO, ArtifactIOBase):
    def __init__(self, instance: 'HttpArtifactInstance', bodypath: Path, polling_delay: float = 0.05):
        """
        Wrapper for the FileIO class that allow pretending our artifacts is a normal file

        Parameters
        ----------
        instance: HttpArtifactInstance
            The artifact instance this FileIO should be linked to
        body_path: Path
            The path to the artifact
        polling_delay: float
            Polling delay in seconds to use when waiting for new data to arrive
        """

        self._instance = instance
        self.polling_delay = polling_delay
        super().__init__(bodypath, mode='rb', closefd=True)

    def __wait_for_completion(self):
        while not self._instance.is_complete:
            time.sleep(self.polling_delay)

    def read(self, size=-1, /) -> bytes:
        if size == -1:
            self.__wait_for_completion()

        while True:
            rd = super().read(size)

            # Detect the end of file
            if len(rd) == 0:
                if not self._instance.is_complete:
                    # Wait a little bit so that the kernel keeps being downloaded
                    time.sleep(self.polling_delay)
                    continue

            return rd

    def readall(self) -> bytes:
        return self.read(-1)

    def seek(self, offset, whence=os.SEEK_SET, /):
        if whence in [os.SEEK_SET, os.SEEK_CUR]:
            # NOTE: Nothing to do since it is legal to move past the end of
            # file, read() will block appropriately when the user tries to read
            # the content at this location
            pass
        else:
            # The whence requires a full artifact, so wait for its completion
            self.__wait_for_completion()

        return super().seek(offset, whence)

    @property
    def content_type(self):
        return self._instance.cached_response.content_type

    @property
    def filesize(self) -> int:
        if filesize := self._instance.filesize:
            return filesize
        else:
            return super().filesize

    @property
    def is_complete(self) -> int:
        return self._instance.is_complete

    @property
    def etag(self) -> str:
        cached_response = self._instance.cached_response
        return cached_response.get("ETag", blake2b(cached_response.serialize().encode()).hexdigest())


class HttpArtifactInstance:
    def __init__(self, artifact: "HttpArtifact", cached_response: CachedResponse, fetch_method: HttpFetchingMethod,
                 body_path: Path, name: str = None):
        """
        Download or resume downloading an artifact's body

        Parameters
        ----------
        artifact : HttpArtifact
            The artifact this instance is for
        cached_response : CachedResponse
            The CachedResponse this body is for
        fetch_method: FetchingMethod
            Records how the artifact instance was fetched
        body_path: Path
            The path to the artifact
        name: str
            The name of the artifact, so that it can be used in log messages
        """

        self.artifact = artifact
        self.cached_response = cached_response
        self.fetch_method = fetch_method
        self.name = name

        # Ensure the artifact is locked while we create a new body
        assert self.artifact._is_locked, "Tried to open a body without holding the artifact lock!"

        self.instance = open(body_path, "rb", buffering=0)

    @property
    def __filepath(self) -> Path:
        # The original path of the file we opened may now point to another file, so
        # the only reliable path for this exact file is our reference in /proc/.
        return Path("/proc/") / str(os.getpid()) / "fd" / str(self.instance.fileno())

    def close(self) -> None:
        self.instance.close()

    @property
    def is_valid(self) -> bool:
        return not self.instance.closed and not HttpArtifactWriter.get_xattr_as_float(self.instance.fileno(),
                                                                                      XATTR_STALE)

    @property
    def is_complete(self) -> bool:
        if HttpArtifactWriter.get_xattr_as_float(self.instance.fileno(), XATTR_COMPLETION_TIME):
            return True
        elif HttpArtifactWriter.get_xattr_as_float(self.instance.fileno(), XATTR_STALE):
            raise StaleHttpArtifactException("The artifact is incomplete and cannot be completed")
        elif not HttpArtifactWriter.has_active_writer(self.__filepath):
            # The process that was downloading the artifact is likely dead... start a new one!
            HttpArtifactWriter(artifact=self.artifact, cached_response=self.cached_response,
                               body_path=self.__filepath, name=self.name)

        return False

    def get_filepath(self, polling_delay: float = 0.05) -> Path:
        """
        Returns a valid filesystem path to a completed artifact.

        If the artifact is not yet complete, poll for its completion every
        `polling_delay` seconds.
        """

        while not self.is_complete:
            time.sleep(polling_delay)  # pragma: nocover

        # Make sure the file has not been closed behind our back
        assert not self.instance.closed, "The backing file is now closed"

        return self.__filepath

    @property
    def creation_time(self) -> float:
        """Returns a unix timestamp of when the artifact instance was created"""

        return HttpArtifactWriter.get_xattr_as_float(self.instance.fileno(), XATTR_START_TIME)

    @property
    def completion_time(self) -> float | None:
        """Returns the number of seconds it took to download the artifact"""

        start = self.creation_time
        end = HttpArtifactWriter.get_xattr_as_float(self.instance.fileno(), XATTR_COMPLETION_TIME)

        if start and end:
            return end - start

    @property
    def resume_count(self) -> int:
        """Returns how many times the download had to be resumed"""
        return round(HttpArtifactWriter.get_xattr_as_float(self.instance.fileno(), XATTR_RESUME_CNT))

    @property
    def filesize(self) -> int:
        return self.cached_response.content_length

    @property
    def filepath(self) -> Path:
        """
        Returns a valid filesystem path to a completed artifact, without the
        default polling delay.

        If you want to control the completion polling delay, use `get_filepath()`.
        """

        return self.get_filepath()

    def open(self, polling_delay: float = 0.05):
        """
        Return a file-like object that
        """

        return HttpArtifactIO(instance=self, bodypath=self.__filepath, polling_delay=polling_delay)


@dataclass
class HttpArtifactPruningReport:
    found: int = 0
    pruned: int = 0
    error: int = 0
    total_bytes: int = 0
    total_seconds: float = 0

    @property
    def total_MiB(self):
        return float(self.total_bytes) / 1024**2


class HttpArtifact:
    """
    Responsible for acquiring instances of an artifact, and handling the HTTP
    requests needed to perform the initial download and further revalidation of
    the content
    """

    def __init__(self, cache_root: DirectoryPath, url: HttpUrl = None,
                 name: str = "<unnamed>", log_callback: LogCallback = None,
                 start_bg_validation: bool = False):
        """
        Create an artifact that can later be acquired

        Parameters
        ----------
        cache_root : DirectoryPath
            The path to the root of the cache directory
        url : HttpUrl
            The URL of the artifact that you want to acquire
        name: str
            The name of the artifact, so that it can be used in log messages
        log_callback : LogCallback
            A function that will be called to report warnings back to the user.
            If missing, messages will be outputted to stdout.
        """

        if not url:
            raise ValueError("The url is empty")

        self.cache_root = Path(cache_root)
        self.url = url
        self.name = name
        self.log_callback = log_callback or print

        self._is_locked = False
        self.__writer = None
        self.__reader = None
        self.__revalidation_lock = Lock()
        self.__revalidation_done_event = Event()
        self.__revalidation_error = None

        if start_bg_validation:
            self.start_background_revalidation()

    @cached_property
    def __url_cache_dir_path(self) -> DirectoryPath:
        """
        Create then return the path to a directory that will be used to store the artifact.

        The path is created based on the hash of the artifact's URL.
        """

        url_hash = blake2b(str(self.url).encode(), digest_size=32).hexdigest()

        path = self.cache_root / url_hash[0:2] / url_hash[2:4] / url_hash[4:]

        try:
            os.makedirs(path, exist_ok=True)
        except PermissionError:  # pragma: no cover
            raise ValueError(f"Permission denied to mkdir \"{path}\"")

        return path

    @cached_property
    def __url_cache_dir_fd(self) -> int:
        """Return an fd to the cache directory, which can be used for flock'ing it"""

        return os.open(self.__url_cache_dir_path, os.O_RDONLY)

    @cached_property
    def __cached_response_path(self) -> Path:
        """Returns the path to the file that will hold the cached response"""

        return self.__url_cache_dir_path / "response.json"

    @cached_property
    def __cached_body_path(self) -> Path:
        """Returns the path to the file that will hold the body of the artifact"""

        return self.__url_cache_dir_path / "body"

    @classmethod
    def _do_get(self, url: HttpUrl, headers: dict[str, str] = {},
                retry: Retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])):
        """
        Perform a GET query with the specified parameters

        Parameters
        ----------
        url : HttpUrl
            The URL of the artifact that you want to acquire
        headers: dict[str, str]
            The list of headers you want to set on the HTTP GET query
        retry : Retry
            The retry object to use in case of errors
        """

        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://", HTTPAdapter(max_retries=retry))

        return session.get(url, stream=True, headers=headers, allow_redirects=True, timeout=10)

    def __get_revalidate_or_reuse_artifact(self) -> (CachedResponse, requests.Response | None, HttpFetchingMethod):
        """
        This function will reuse a cached artifact if it is still fresh,
        revalidate it, or get the artifact if we did not have it.
        """

        req_headers = {}
        cached_response = None

        # Before trying to reuse a response, check if a body writer may have already marked
        # the current body as STALE, which would be the strongest invalidation we could get
        if not HttpArtifactWriter.get_xattr_as_float(self.__cached_body_path, XATTR_STALE):
            # Check if we have an existing response we may be able to reuse
            # NOTE: We ignore cached responses for the wrong URL (2 URLs generating the
            # same blake2 hash)
            cached_response = CachedResponse.from_file(self.__cached_response_path)
            # TODO: Perform validation of the artifact to ensure it did not bitrot and is actually complete
            if cached_response and cached_response.url == self.url and self.__cached_body_path.exists():
                cache_tags = cached_response.tags

                # Check if what we have in cache is still considered valid (not expired)
                if HttpArtifactWriter.has_active_writer(self.__cached_body_path):
                    return cached_response, None, HttpFetchingMethod.IN_FLIGHT_REUSE
                elif cache_tags.is_fresh:
                    return cached_response, None, HttpFetchingMethod.FRESH_CACHE_REUSE
                elif cache_tags.can_revalidate:
                    # We have data that make be re-used once re-validated
                    req_headers.update(cached_response.revalidatation_headers())
                else:
                    # We can't re-use anything, so pretend our cached response didn't exist
                    cached_response = None
            else:
                cached_response = None

        # The existing cache entry could not be re-used immediately, re-validate or re-download the artifact
        request = self._do_get(url=self.url, headers=req_headers)

        # Update or create our cached response, then write it to disk
        if cached_response:
            cached_response.update(request)
        else:
            cached_response = CachedResponse.from_request_response(request)
        cached_response.save(self.__cached_response_path)

        return cached_response, request, None

    def __lock(self):
        """Acquire an exclusive lock of the cache directory"""

        if not self._is_locked:
            fcntl.flock(self.__url_cache_dir_fd, fcntl.LOCK_EX)

            # Keep track of our lock status for ease of checking
            self._is_locked = True

            # Reset the mtime every time we lock to indicate we read this cache entry
            self.__url_cache_dir_path.touch()

    def __unlock(self):
        """Release the lock on the cache directory"""

        assert self._is_locked, "Tried to unlock while not being locked"

        fcntl.flock(self.__url_cache_dir_fd, fcntl.LOCK_UN)
        self._is_locked = False

    def __handle_revalidation(self):
        """
        This thread performs the revalidation or the artifact before creating a reader/writer.
        """

        # Prevent other threads from performing concurrent validation since flocks are reentrant
        with self.__revalidation_lock:
            # Lock the artifact ahead of performing background revalidation
            self.__lock()

            try:
                # Make sure another thread did not already perform the revalidation while we were waiting for the lock
                if self.__revalidation_done_event.is_set():
                    return

                cached_response, request, fetch_method = self.__get_revalidate_or_reuse_artifact()

                # If a request was made, we may need to start a new writer!
                writer = None
                if request is not None:
                    if request.status_code >= 200 and request.status_code < 300:
                        if fetch_method is None:
                            fetch_method = HttpFetchingMethod.FULL_DOWNLOAD

                        # The body file cannot be re-used, so start a body writer to update it
                        writer = HttpArtifactWriter(artifact=self, cached_response=cached_response,
                                                    body_path=self.__cached_body_path, name=self.name, request=request)
                    else:
                        request.close()

                        if request.status_code == 304:
                            fetch_method = HttpFetchingMethod.REUSE_AFTER_REVALIDATION
                        elif (request.status_code in [500, 502, 503, 504]
                              and CacheState.REUSE_ON_ERROR in cached_response.tags
                              and HttpArtifactWriter.get_xattr_as_float(self.__cached_body_path,
                                                                        XATTR_COMPLETION_TIME)):
                            # If our cached response allowed for re-use when receiving an error and we had a complete
                            # response, re-use it!
                            fetch_method = HttpFetchingMethod.REUSE_DUE_TO_ERROR
                        else:
                            raise ValueError(f"Failed to access the artifact - Got status {request.status_code}")

                # Assert that we actually have a body
                if not self.__cached_body_path.exists():  # pragma: nocover
                    raise ValueError(f"ASSERT: Expected to have a body - {cached_response}, {request}, {fetch_method}")

                # Create the reader
                reader = HttpArtifactInstance(artifact=self, cached_response=cached_response, fetch_method=fetch_method,
                                              body_path=self.__cached_body_path, name=self.name)

                # Restart the download if the artifact was incomplete
                reader.is_complete

                # Signal that we are done with the revalidation
                self.__reader = reader
                self.__writer = writer
            except Exception as e:
                self.__revalidation_error = e
            finally:
                self.__revalidation_done_event.set()
                self.__unlock()

    def start_background_revalidation(self):
        # Make sure that it was not already done
        if self.__revalidation_done_event.is_set():
            return

        # Start the validation process
        Thread(target=self.__handle_revalidation, name=f"HttpArtifactRevalidation-{self.name}").start()

    @property
    def is_instance_available(self) -> bool:
        """Returns True if `get_instance()` will not block, False otherwise."""

        return self.__revalidation_done_event.is_set()

    def get_instance(self) -> HttpArtifactInstance:
        """Returns an instance of the artifact"""

        # Ensure that validation has happened before continuing
        self.start_background_revalidation()

        if not self.is_instance_available:  # pragma: nocover
            self.__revalidation_done_event.wait()

        # If we hit an error during revalidation, raise it here to let users know!
        if self.__revalidation_error is not None:
            raise self.__revalidation_error from None

        return self.__reader

    def __enter__(self):
        return self.get_instance()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__reader.close()

        # Wait for the writer thread to be done if we had started it to make the cache valid
        if self.__writer:
            self.__writer.join()

    @property
    def last_access(self) -> datetime:
        """Returns the last time the cache was accessed"""

        # NOTE: We use the cache dir's mtime to keep track of the last access
        #       time (see lock()) since many users run using noatime
        # NOTE: The mtime is stored as a timestamp in UTC timezone on UNIX systems
        return datetime.fromtimestamp(self.__url_cache_dir_path.stat().st_mtime, tz=UTC)


class HttpArtifactCache:
    def __init__(self, cache_root: DirectoryPath, log_callback: LogCallback = None,
                 start_bg_validation: bool = False):
        """
        An helper class designed to cache ready-made artifacts and instances so
        that artifact revalidation happens at most once per execution.

        Parameters
        ----------
        cache_root : DirectoryPath
            The path to the root of the cache directory
        log_callback : LogCallback
            The log callback function to use on error or when something important happens
        """

        self.root_path = cache_root
        self.log_callback = log_callback
        self.start_bg_validation = start_bg_validation

        self.cached_artifacts_lck = RLock()
        self.cached_artifacts = dict()

    def __create_artifact(self, url: HttpUrl, name: str = None) -> HttpArtifact:
        with self.cached_artifacts_lck:
            artifact = self.cached_artifacts[url] = HttpArtifact(cache_root=self.root_path,
                                                                 log_callback=self.log_callback,
                                                                 url=url, name=name,
                                                                 start_bg_validation=self.start_bg_validation)
        return artifact

    def get_or_reuse_artifact(self, url: HttpUrl, name: str = None) -> HttpArtifact:
        with self.cached_artifacts_lck:
            if artifact := self.cached_artifacts.get(url):
                return artifact
            else:
                return self.__create_artifact(url=url, name=name)

    def get_or_reuse_instance(self, url: HttpUrl, name: str = None) -> HttpArtifactInstance:
        with self.cached_artifacts_lck:
            artifact = self.get_or_reuse_artifact(url=url, name=name)

            if not artifact.is_instance_available:
                self.log_callback(f"Waiting for [{name}]({url}) to finish revalidation")
            instance = artifact.get_instance()

            # Make sure the instance is valid, otherwise restart the download
            if not instance or not instance.is_valid:
                instance = self.__create_artifact(url=url, name=name).get_instance()

            return instance

    def prune_artifacts(self, unused_for: timedelta = timedelta(days=60)) -> HttpArtifactPruningReport:
        """
        Removes artifacts that were left unused for the specified amount of time

        Parameters
        ----------
        unused_for: timedelta
            The amount of time an artifact should have gone unused for before being deleted
        """
        r = HttpArtifactPruningReport()

        # Start by ensuring that only one removal process happens at a time
        try:
            cache_root_fd = os.open(self.root_path, os.O_RDONLY)
            try:
                fcntl.flock(cache_root_fd, fcntl.LOCK_EX)

                start = time.time()

                for root, dirs, files in os.walk(self.root_path):
                    # Look for leaf directories
                    if dirs == [] and "response.json" in files:
                        r.found += 1
                        try:
                            # NOTE: This is inherently racy but let's just say that it is *very* unlikely to happen
                            if (time.time() - os.stat(root).st_mtime) > unused_for.total_seconds():
                                # Compute the size of the folder before deletion
                                folder_size = sum(f.stat().st_size for f in Path(root).glob('**/*') if f.is_file())

                                # Delete the folder
                                shutil.rmtree(root)

                                # Only update the stats when we succeeded in removing the folder
                                r.pruned += 1
                                r.total_bytes += folder_size
                        except Exception:
                            self.log_callback(traceback.format_exc())
                            r.error += 1

                r.total_seconds = time.time() - start
            finally:
                # NOTE: Closing the fd will automatically remove the lock
                os.close(cache_root_fd)
        except Exception:
            self.log_callback(traceback.format_exc())

        return r
