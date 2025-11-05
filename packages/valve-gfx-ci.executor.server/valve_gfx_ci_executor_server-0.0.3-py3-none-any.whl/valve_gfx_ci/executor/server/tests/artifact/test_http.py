from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha1, file_digest
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch, call, PropertyMock
import email.utils
import fcntl
import time
import os

from freezegun import freeze_time
from requests.packages.urllib3.util.retry import Retry
import pytest
import requests.exceptions

from server.artifact.http import CacheState, CachedResponse, StaleHttpArtifactException, HttpArtifactIO
from server.artifact.http import XATTR_START_TIME, XATTR_COMPLETION_TIME, XATTR_RESUME_CNT, XATTR_STALE
from server.artifact.http import HttpArtifactWriter, HttpFetchingMethod, HttpArtifactInstance, HttpArtifactPruningReport
from server.artifact.http import HttpArtifact, HttpArtifactCache


def NamedTemporaryFileWithXAttrRights(*args, **kwargs):
    # Workaround for the fd.o runners not allowing extended attributes in /tmp
    for dir_src in [None, "/"]:
        r = NamedTemporaryFile(*args, **kwargs, dir=dir_src)
        try:
            os.setxattr(r.name, b"user.pytest.xattr_check", b'1')
            return r
        except OSError:  # pragma: nocover
            pass

    # We did not find a location that worked, so let's raise an exception
    raise ValueError("Can't find a location where we can create files with extended attributes")  # pragma: nocover


# CacheState

def test_CacheState__is_reusable():
    assert CacheState.NO_TAGS.is_reusable

    assert not CacheState.NO_STORE.is_reusable
    assert not CacheState.UNCACHEABLE_STATUS_CODE.is_reusable


def test_CacheState__can_revalidate():
    assert not CacheState.NO_TAGS.can_revalidate
    assert CacheState.HAS_ETAG.can_revalidate
    assert CacheState.HAS_LAST_MODIFIED.can_revalidate


def test_CacheState__is_fresh():
    assert CacheState.FRESH.is_fresh
    assert not (CacheState.UNCACHEABLE_STATUS_CODE | CacheState.FRESH).is_fresh


# CachedResponse

CR_GITLAB = CachedResponse(
    url="https://gitlab.freedesktop.org/mupuf/boot2container/-/releases/v0.9.10/downloads/linux-arm64.firmware.cpio.xz",
    status_code=200,
    headers={
        "date": "Mon, 20 May 2024 07:28:20 GMT",
        "content-type": "binary/octet-stream",
        "content-length": "25282048",
        "connection": "keep-alive",
        "accept-ranges": "bytes",
        "cache-control": "max-age=0, private, must-revalidate",
        "etag": "\"f2fa78618424510f9050d5c7107fdebf-3\"",
        "last-modified": "Mon, 22 May 2023 13:05:16 GMT",
        "vary": "Origin",
        "x-amz-request-id": "tx000008995f20580331ec2-00664afb94-71f1a1-fdo-s3-dc",
        "x-content-type-options": "nosniff",
        "x-frame-options": "SAMEORIGIN",
        "x-gitlab-meta": "{\"correlation_id\":\"01HYAEDFB956WF9E15CG7RRFD3\",\"version\":\"1\"}",
        "x-request-id": "01HYAEDFB956WF9E15CG7RRFD3",
        "x-rgw-object-type": "Normal",
        "x-runtime": "0.043891",
        "strict-transport-security": "max-age=15724800; includeSubDomains"
    },
    created_at="Mon, 20 May 2024 07:28:19 +0000"
)

CR_NGINX = CachedResponse(
    url="https://fs.mupuf.org/hdk8650/initramfs.linux_arm64.cpio.xz",
    status_code=200,
    headers={
        "server": "nginx/1.14.2",
        "date": "Sun, 19 May 2024 11:31:27 GMT",
        "content-type": "text/plain",
        "content-length": "19225600",
        "last-modified": "Thu, 28 Mar 2024 10:30:28 GMT",
        "connection": "keep-alive",
        "etag": "\"660546c4-1255c00\"",
        "accept-ranges": "bytes"
    },
    created_at="Sun, 19 May 2024 11:31:28 +0000"
)

CR_S3 = CachedResponse(
    url="https://s3.freedesktop.org/artifacts/mupuf/mesa/1355743/mesa-arm32-default-debugoptimized.tar.zst",
    status_code=200,
    headers={
        "date": "Fri, 31 Jan 2025 12:00:00 GMT",
        "content-type": "application/octet-stream",
        "content-length": "157041952",
        "accept-ranges": "bytes",
        "last-modified": "Fri, 31 Jan 2025 10:52:49 GMT",
        "x-amz-expiration": 'expiry-date="Mon, 03 Mar 2025 00:00:00 GMT", rule-id="Expiration Rule"',
        "x-rgw-object-type": "Normal",
        "etag": '"1168404e0ca3fda05bb90205d9f24038-15"',
        "expires": "Fri Feb 28 10:52:37 2025",
        "x-amz-request-id": "tx0000050c5ff34aad4fc1f-00679cb217-11d7baf-fdo-opa-dc",
        "x-envoy-upstream-service-time": "67",
        "x-envoy-decorator-operation": "rook-ceph-rgw-fdo-opa-dc.rook-ceph.svc.cluster.local:80/*",
        "strict-transport-security": "max-age=15724800; includeSubDomains",
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET,HEAD,OPTIONS",
        "access-control-allow-headers": ("DNT,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,"
                                         "Cache-Control,Content-Type"),
        "access-control-max-age": "1728000"
    },
    created_at="Fri, 31 Jan 2025 12:00:01 +0000"
)


def test_CachedResponse_no_headers():
    with freeze_time(datetime(2024, 5, 22, 12, 0, 0).isoformat()):
        r = CachedResponse(url="http://host.tld/", status_code=204, headers={"KeY": "Value"}, created_at=None)

        assert r.url == "http://host.tld/"
        assert r.status_code == 204
        assert r.headers == {"key": "Value"}

        assert r.content_length is None

        # Make sure created_at is set if missing
        assert r.created_at == "Wed, 22 May 2024 12:00:00 +0000"

        # Make sure that we fallback to the client date if the server date is missing
        assert r.server_date == datetime(year=2024, month=5, day=22, hour=12, minute=0, second=0, tzinfo=timezone.utc)

        assert r.cache_control == {}
        assert r.accept_ranges is None
        assert r.tags == CacheState.NO_TAGS
        assert r.revalidatation_headers() == {}

        assert str(r) == "<CachedResponse NO_TAGS>"


def test_CachedResponse__gitlab():
    r = CR_GITLAB

    assert r.content_type == "binary/octet-stream"
    assert r.content_length == 25282048

    with freeze_time(datetime(2024, 5, 22, 12, 0, 0).isoformat()):
        assert r.age == timedelta(days=2, seconds=16301)
        assert r.client_date == datetime(year=2024, month=5, day=20, hour=7, minute=28, second=19, tzinfo=timezone.utc)
        assert r.server_date == datetime(year=2024, month=5, day=20, hour=7, minute=28, second=20, tzinfo=timezone.utc)
        assert r.cache_control == {'max-age': timedelta(0), 'must-revalidate': None, 'private': None}
        assert r.accept_ranges == "bytes"
        assert (repr(r.tags) ==
                "<CacheState.HAS_EXPIRATION|HAS_LAST_MODIFIED|HAS_ETAG|ACCEPTS_RANGES|NO_CACHE: 188>")
        assert r.revalidatation_headers() == {
           'If-Modified-Since': 'Mon, 22 May 2023 13:05:16 GMT',
           'If-None-Match': '"f2fa78618424510f9050d5c7107fdebf-3"'
        }


def test_CachedResponse__nginx():
    r = CR_NGINX

    assert r.content_type == "text/plain"
    assert r.content_length == 19225600

    with freeze_time(datetime(2024, 5, 22, 12, 0, 0).isoformat()):
        assert r.age == timedelta(days=3, seconds=1712)

        assert r.client_date == datetime(year=2024, month=5, day=19, hour=11, minute=31, second=28, tzinfo=timezone.utc)
        assert r.server_date == datetime(year=2024, month=5, day=19, hour=11, minute=31, second=27, tzinfo=timezone.utc)
        assert r.cache_control == {}
        assert r.accept_ranges == "bytes"
        assert (repr(r.tags) ==
                "<CacheState.HAS_EXPIRATION|HAS_LAST_MODIFIED|HAS_ETAG|ACCEPTS_RANGES|FRESH: 316>")
        assert r.revalidatation_headers() == {
           'If-Modified-Since': 'Thu, 28 Mar 2024 10:30:28 GMT',
           'If-None-Match': '"660546c4-1255c00"'
        }


def test_CachedResponse__s3():
    r = CR_S3

    assert r.content_type == "application/octet-stream"
    assert r.content_length == 157041952

    with freeze_time(datetime(2025, 1, 31, 16, 30, 0).isoformat()):
        assert r.age == timedelta(hours=4, minutes=29, seconds=59)

        assert r.client_date == datetime(year=2025, month=1, day=31, hour=12, minute=0, second=1, tzinfo=timezone.utc)
        assert r.server_date == datetime(year=2025, month=1, day=31, hour=12, minute=0, second=0, tzinfo=timezone.utc)
        assert r.cache_control == {}
        assert r.accept_ranges == "bytes"
        assert (repr(r.tags) ==
                "<CacheState.HAS_EXPIRATION|HAS_LAST_MODIFIED|HAS_ETAG|ACCEPTS_RANGES|FRESH: 316>")
        assert r.revalidatation_headers() == {
           'If-Modified-Since': "Fri, 31 Jan 2025 10:52:49 GMT",
           'If-None-Match': '"1168404e0ca3fda05bb90205d9f24038-15"'
        }


def test_CachedResponse__tags__invalid_status_code():
    r = CachedResponse(url="", status_code=404, headers={})
    assert CacheState.UNCACHEABLE_STATUS_CODE in r.tags

    r = CachedResponse(url="", status_code=200, headers={})
    assert CacheState.UNCACHEABLE_STATUS_CODE not in r.tags


def test_CachedResponse__tags__no_store():
    r = CachedResponse(url="", status_code=206, headers={"Cache-Control": "no-store"})
    assert CacheState.NO_STORE in r.tags

    r = CachedResponse(url="", status_code=206, headers={"Cache-Control": "no-store, must-understand"})
    assert CacheState.NO_STORE not in r.tags


def test_CachedResponse__tags__no_cache():
    r = CachedResponse(url="", status_code=206, headers={"Cache-Control": "no-cache"})
    assert CacheState.NO_CACHE in r.tags

    r = CachedResponse(url="", status_code=206, headers={"Cache-Control": "must-revalidate"})
    assert CacheState.NO_CACHE in r.tags

    r = CachedResponse(url="", status_code=206, headers={"Pragma": "no-cache"})
    assert CacheState.NO_CACHE in r.tags


def test_CachedResponse__tags__fresh():
    def get_tags(max_age, expires_delta):
        expires = email.utils.format_datetime(datetime.now(tz=timezone.utc) + expires_delta)
        r = CachedResponse(url="", status_code=200, headers={"Cache-Control": f"max-age={max_age}",
                                                             "Expires": expires})
        return r.tags

    # Both Expires and max-age set in the future
    assert CacheState.FRESH in get_tags(max_age=60, expires_delta=timedelta(30))

    # Expires in the past but max_age in future
    assert CacheState.FRESH not in get_tags(max_age=60, expires_delta=timedelta(-30))

    # Max age expired now, Expires in the future
    assert CacheState.FRESH not in get_tags(max_age=0, expires_delta=timedelta(30))

    # Both max-age and Expires expired
    assert CacheState.FRESH not in get_tags(max_age=0, expires_delta=timedelta(-30))


def test_CachedResponse__tags__stale():
    # Fresh artifacts do not get the STALE tags
    r = CachedResponse(url="", status_code=200,
                       headers={"Cache-Control": "max-age=60, stale-while-revalidate=1, stale-if-error=1"})
    assert r.tags == CacheState.HAS_EXPIRATION | CacheState.FRESH

    # Expired artifact, but can revalidate and reuse on error
    r = CachedResponse(url="", status_code=200,
                       headers={"Cache-Control": "max-age=0, stale-while-revalidate=60, stale-if-error=60"})
    assert repr(r.tags) == "<CacheState.HAS_EXPIRATION|REUSE_WHILE_REVALIDATE|REUSE_ON_ERROR: 1540>"

    # Expired artifact, can reuse during revalidation, but not on error
    r = CachedResponse(url="", status_code=200,
                       headers={"Cache-Control": "max-age=0, stale-while-revalidate=60, stale-if-error=0"})
    assert repr(r.tags) == "<CacheState.HAS_EXPIRATION|REUSE_WHILE_REVALIDATE: 516>"

    # Expired artifact, can reuse on error but not during revalidation
    r = CachedResponse(url="", status_code=200,
                       headers={"Cache-Control": "max-age=0, stale-while-revalidate=0, stale-if-error=60"})
    assert repr(r.tags) == "<CacheState.HAS_EXPIRATION|REUSE_ON_ERROR: 1028>"

    # Expired artifact and can't reuse
    r = CachedResponse(url="", status_code=200,
                       headers={"Cache-Control": "max-age=0, stale-while-revalidate=0, stale-if-error=0"})
    assert repr(r.tags) == "<CacheState.HAS_EXPIRATION: 4>"


def test_CachedResponse__tags__misc():
    r = CachedResponse(url="", status_code=200,
                       headers={"Cache-Control": "immutable"})
    assert r.tags == CacheState.IMMUTABLE


def test_revalidation__headers():
    r = CachedResponse(url="", status_code=200, headers=dict(CR_NGINX.headers))

    assert r.revalidatation_headers() == {
        'If-Modified-Since': 'Thu, 28 Mar 2024 10:30:28 GMT',
        'If-None-Match': '"660546c4-1255c00"'
    }

    # Remove the ETag header
    del r.headers["etag"]
    assert r.revalidatation_headers() == {
        'If-Modified-Since': 'Thu, 28 Mar 2024 10:30:28 GMT',
    }

    # Remove the Last-Modified header
    del r.headers["last-modified"]
    assert r.revalidatation_headers() == {}


def test_CachedResponse__update():
    orig = CachedResponse(url="orig", status_code=200, headers={}, created_at="Wed, 22 May 2024 00:00:00 +0000")

    # Make sure that an uncacheable response does not change our cached response
    r = deepcopy(orig)
    r.update(MagicMock(url="new", status_code=100))
    assert r == orig

    # Ensure a revalidation updates created_at and the headers
    r = deepcopy(orig)
    r.update(MagicMock(url="new", status_code=304, headers={"key": "value"}))
    assert r.url == orig.url
    assert r.status_code == orig.status_code
    assert r.headers == {"key": "value"}
    assert r.client_date > orig.client_date

    # Ensure a cacheable status updates every field but the address
    r = deepcopy(orig)
    r.update(MagicMock(url="new", status_code=204, headers={"key": "value"}))
    assert r.url == orig.url
    assert r.status_code == 204
    assert r.headers == {"key": "value"}
    assert r.client_date > orig.client_date


def test_CachedResponse__save_load():
    # Check that saving and reloading from file results in the same object
    with NamedTemporaryFileWithXAttrRights() as f:
        CR_NGINX.save(f.name)
        assert CachedResponse.from_file(f.name) == CR_NGINX


def test_CachedResponse__from_request_response():
    # No history
    rr = MagicMock(url="final_url", status_code=200, headers={"Hello": "World"})
    r = CachedResponse.from_request_response(rr)
    assert r.url == rr.url
    assert r.status_code == rr.status_code
    assert r.headers == {"hello": "World"}  # NOTE: Keys are lowered on import

    # With history
    rr = MagicMock(url="final_url", status_code=200, headers={"Hello": "World"}, history=[MagicMock(url="first_url")])
    r = CachedResponse.from_request_response(rr)
    assert r.url == "first_url"


# HttpArtifactWriter

def test_HttpArtifactWriter__fresh_download_without_lock_raises():
    with pytest.raises(AssertionError) as exc:
        HttpArtifactWriter(artifact=MagicMock(_is_locked=False), cached_response=CR_NGINX,
                           body_path="/body", request=MagicMock())
    assert "Tried to create a new body without holding the artifact lock!" in str(exc)


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


def test_HttpArtifactWriter__fresh_download():
    @static_vars(call_count=0)
    def mock_iter_content(size: int):
        assert size == 16384
        assert HttpArtifactWriter.has_active_writer(body.name)

        if mock_iter_content.call_count == 3:
            raise requests.exceptions.StreamConsumedError()
        else:
            mock_iter_content.call_count += 1
            yield b"CONTENT"

    artifact = MagicMock(_is_locked=True)
    request = MagicMock(iter_content=mock_iter_content)

    with NamedTemporaryFileWithXAttrRights() as body:
        orig_inode = os.stat(body.name).st_ino
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_START_TIME, default=-1.0) == -1.0
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_COMPLETION_TIME, default=-1.0) == -1.0
        assert not HttpArtifactWriter.has_active_writer(body.name)

        w = HttpArtifactWriter(artifact=artifact, cached_response=CR_NGINX, body_path=body.name, request=request)
        w.join()

        # Make sure the HttpArtifactWriter replaced the file without re-using it
        assert orig_inode != os.stat(body.name).st_ino

        # Make sure the start/completion times got written
        start = HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_START_TIME, default=-1.0)
        completion = HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_COMPLETION_TIME, default=-1.0)
        assert (time.time() - start) < 5.0
        assert (time.time() - completion) < 5.0
        assert completion > start

        # Make sure that XATTR_RESUME_CNT was not set (we did not have to resume)
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_RESUME_CNT, default=-1.0) == -1.0

        # Check the content that was written to the file
        assert open(body.name, "rb").read() == b"CONTENTCONTENTCONTENT"


def test_HttpArtifactWriter__early_abort():
    with NamedTemporaryFileWithXAttrRights() as body:
        # Set a completion time to get an early abort
        os.setxattr(body.fileno(), XATTR_COMPLETION_TIME, str(123456).encode())

        w = HttpArtifactWriter(artifact=None, cached_response=CR_NGINX, body_path=body.name, request=None)

        # Make sure we never start the download
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_START_TIME, default=-1.0) < 0

        # Ensure the thread never got started
        assert w.native_id is None


def test_HttpArtifactWriter__resume__with_etag_and_partial_range():
    ORIGINAL_DATA = b"ORIGINAL"
    RESUME_DATA = b"RESUME"

    @static_vars(call_count=0)
    def mock_iter_content(size: int):
        mock_iter_content.call_count += 1

        if mock_iter_content.call_count == 4:
            raise requests.exceptions.StreamConsumedError()
        elif (mock_iter_content.call_count % 2) == 0:
            raise ValueError("Random error")
        else:
            yield RESUME_DATA

    @static_vars(call_count=-1)
    def mock_do_get(url, headers):
        mock_do_get.call_count += 1

        cur_loc = len(ORIGINAL_DATA) + mock_do_get.call_count * len(RESUME_DATA)

        assert url == CR_NGINX.url
        assert headers == {
            "Range": f"bytes={cur_loc}-",
            "If-Unmodified-Since": CR_NGINX.get("Last-Modified"),
            "If-Range": CR_NGINX.get("ETag")
        }

        return MagicMock(
            url=CR_NGINX.url, status_code=206, iter_content=mock_iter_content,
            headers={
                "Etag": CR_NGINX.get("Etag"),
                "Last-Modified": CR_NGINX.get("Last-Modified"),
                "Content-Range": f"bytes={cur_loc}-123456"
            })

    artifact = MagicMock(_is_locked=False, _do_get=MagicMock(side_effect=mock_do_get))

    with NamedTemporaryFileWithXAttrRights() as body:
        orig_inode = os.stat(body.name).st_ino

        # Write some original content before rewinding to make sure nothing gets rewritten
        body.write(ORIGINAL_DATA)
        body.seek(0)

        # Set a start time
        os.setxattr(body.fileno(), XATTR_START_TIME, str(123456).encode())

        # Start the writer
        w = HttpArtifactWriter(artifact=artifact, cached_response=CR_NGINX, body_path=body.name)
        w.join()

        # Make sure the HttpArtifactWriter reuse the same file
        assert orig_inode == os.stat(body.name).st_ino

        # Make sure the start time was not changed
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_START_TIME) == 123456

        # Make sure the completion time got written
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_COMPLETION_TIME) > 0

        # Count how many times we resumed
        assert HttpArtifactWriter.get_xattr_as_float(body.name, XATTR_RESUME_CNT) == 2.0

        # Check the content that was written to the file
        assert open(body.name, "rb").read() == b"ORIGINALRESUMERESUME"

        # Check the generated logs
        assert artifact.log_callback.call_count == 3
        assert (artifact.log_callback.call_args_list[0] ==
            call('[<unnamed>] Resuming download at 8 bytes using the following headers: Range, If-Unmodified-Since, If-Range'))  # noqa
        assert "ValueError: Random error\n" in artifact.log_callback.call_args_list[1].args[0]

        assert (artifact.log_callback.call_args_list[2] ==
            call('[<unnamed>] Resuming download at 14 bytes using the following headers: Range, If-Unmodified-Since, If-Range'))  # noqa


def test_HttpArtifactWriter__gen_resume_headers():
    cr = deepcopy(CR_NGINX)

    assert HttpArtifactWriter._gen_resume_headers(42, cr) == {
        "Range": "bytes=42-",
        "If-Unmodified-Since": cr.get("Last-Modified"),
        "If-Range": cr.get("ETag")
    }

    # Try again without the ETag
    del cr.headers["etag"]
    assert HttpArtifactWriter._gen_resume_headers(84, cr) == {
        "Range": "bytes=84-",
        "If-Unmodified-Since": cr.get("Last-Modified"),
        "If-Range": cr.get("Last-Modified")
    }

    # Don't resume if we are at the 0 bytes position
    assert HttpArtifactWriter._gen_resume_headers(0, cr) == {}

    # Remove Accepts Range
    del cr.headers["accept-ranges"]
    assert HttpArtifactWriter._gen_resume_headers(42, cr) == {}


def test_HttpArtifactWriter__validate_resume_response__fields_dont_match():
    name = "name"

    # Check what happens when fields don't match
    request_response = MagicMock(url="url", status_code=206, headers={})
    with NamedTemporaryFileWithXAttrRights() as writer:
        with pytest.raises(ValueError) as exc:
            HttpArtifactWriter._validate_resume_response(name=name, writer=writer,
                                                         cached_response=CR_NGINX, request_response=request_response)
        msg = f"[{name}] The file changed and requires a full redownload. Changed fields: ['Etag', 'Last-Modified']"
        assert msg in str(exc)

        # Make sure the artifact was marked as stale
        assert HttpArtifactWriter.get_xattr_as_float(writer.name, XATTR_STALE) == 1.0


def test_HttpArtifactWriter__validate_resume_response__resume_without_content_range():
    name = "name"
    headers = deepcopy(CR_NGINX.headers)
    request_response = MagicMock(url="url", status_code=206, headers=headers)
    with NamedTemporaryFileWithXAttrRights() as writer:
        with pytest.raises(ValueError) as exc:
            HttpArtifactWriter._validate_resume_response(name=name, writer=writer,
                                                         cached_response=CR_NGINX, request_response=request_response)
        msg = f"[{name}] Content-Range is missing from the headers despite a 206 status code"
        assert msg in str(exc)


def test_HttpArtifactWriter__validate_resume_response__complete_restart():
    name = "name"
    request_response = MagicMock(url="url", status_code=200, headers=CR_NGINX.headers)
    with NamedTemporaryFileWithXAttrRights() as writer:
        writer.write(b"CONTENT")
        assert writer.tell() > 0

        r = HttpArtifactWriter._validate_resume_response(name=name, writer=writer,
                                                         cached_response=CR_NGINX, request_response=request_response)
        assert r == request_response

        # Check that we rewinded the writer to the start
        assert writer.tell() == 0


def test_HttpArtifactWriter__validate_resume_response__unexpected_status_code():
    name = "name"
    request_response = MagicMock(url="url", status_code=204, headers=CR_NGINX.headers)
    with NamedTemporaryFileWithXAttrRights() as writer:
        with pytest.raises(ValueError) as exc:
            HttpArtifactWriter._validate_resume_response(name=name, writer=writer,
                                                         cached_response=CR_NGINX, request_response=request_response)
        msg = f"[{name}] Unexpected status code: 204"
        assert msg in str(exc)


def test_HttpArtifactWriter_has_active_writer():
    assert not HttpArtifactWriter.has_active_writer(None)


# HttpArtifactIO

def setup_HttpArtifactIO(content=b"Hello world",
                         is_complete_mock=PropertyMock(side_effect=[False, False, False, True])):
    instance = MagicMock(cached_response=CR_NGINX)
    type(instance).is_complete = is_complete_mock

    with NamedTemporaryFileWithXAttrRights(delete=False) as body:
        body.write(content)

    return HttpArtifactIO(instance, body.name, polling_delay=0.0)


def test_HttpArtifactIO__read__partial_read():
    is_complete_mock = PropertyMock(side_effect=[False, False, False, True])
    f = setup_HttpArtifactIO(b"Hello world", is_complete_mock)

    assert f.read(5) == b"Hello"
    assert f.read(6) == b" world"

    # We are at the end of the file, try reading more data and ensure that
    # we only return when is_complete is True
    assert is_complete_mock.call_count == 0
    assert f.read(5) == b""
    assert is_complete_mock.call_count == 4


def test_HttpArtifactIO__read__all():
    is_complete_mock = PropertyMock(side_effect=[False, False, False, True])
    f = setup_HttpArtifactIO(b"Hello world", is_complete_mock)

    assert is_complete_mock.call_count == 0
    assert f.read(-1) == b"Hello world"
    assert is_complete_mock.call_count == 4


def test_HttpArtifactIO__readall():
    is_complete_mock = PropertyMock(side_effect=[False, False, False, True])
    f = setup_HttpArtifactIO(b"Hello world", is_complete_mock)
    assert f.readall() == b"Hello world"


def test_HttpArtifactIO__seek():
    is_complete_mock = PropertyMock(side_effect=[False, True])
    f = setup_HttpArtifactIO(b"Hello world", is_complete_mock)

    # Absolute and relative seeks should not check for completion
    assert f.seek(128, os.SEEK_SET) == 128
    assert f.seek(128, os.SEEK_CUR) == 256
    assert is_complete_mock.call_count == 0

    # Seeks from the end should wait for completion before returning
    assert f.seek(0, os.SEEK_END) == 11
    assert is_complete_mock.call_count == 2


def test_HttpArtifactIO__filesize():
    f = setup_HttpArtifactIO()

    # Check that if the filesize is known, we return it directly
    f._instance.filesize = 4242
    assert f.filesize == 4242

    # Check that if the filesize is unknown, we try seeking and fail
    # if the artifact isn't seekable
    f._instance.filesize = None
    f.seekable = lambda: False
    with pytest.raises(ValueError) as exc:
        f.filesize
    assert "The artifact does not provide a filesize nor can be seeked" in str(exc)

    # Check that if the filesizse is unknown, we try seeking
    f._instance.filesize = None
    f.seekable = lambda: True
    f.tell = lambda: 1337
    f.seek = MagicMock(return_value=12345)
    assert f.filesize == 12345
    f.seek.assert_has_calls(calls=[
            call(0, os.SEEK_END),
            call(1337, os.SEEK_SET)])


def test_HttpArtifactIO__content_type():
    f = setup_HttpArtifactIO()

    assert f.content_type == "text/plain"


def test_HttpArtifactIO__is_complete():
    f = setup_HttpArtifactIO()
    f._instance.is_complete = MagicMock()
    assert f.is_complete == f._instance.is_complete


def test_HttpArtifactIO__etag():
    f = setup_HttpArtifactIO()
    assert f.etag == '"660546c4-1255c00"'


# HttpArtifactInstance

def test_HttpArtifactInstance__artifact_not_locked():
    with pytest.raises(AssertionError) as exc:
        HttpArtifactInstance(artifact=MagicMock(_is_locked=False), cached_response=CR_NGINX,
                             fetch_method=HttpFetchingMethod.FULL_DOWNLOAD, body_path="")
    assert "Tried to open a body without holding the artifact lock!" in str(exc)


def test_HttpArtifactInstance__fresh_and_complete_cache():
    artifact = MagicMock(_is_locked=True)
    body_content = b"Hi, I'm a full body!"

    with NamedTemporaryFileWithXAttrRights() as body:
        body.write(body_content)
        body.flush()

        # Pretend the body is complete
        os.setxattr(body.fileno(), XATTR_RESUME_CNT, str(2).encode())
        os.setxattr(body.fileno(), XATTR_START_TIME, str(100000).encode())
        os.setxattr(body.fileno(), XATTR_COMPLETION_TIME, str(123456).encode())

        instance = HttpArtifactInstance(artifact=artifact, cached_response=CR_NGINX,
                                        fetch_method=HttpFetchingMethod.FRESH_CACHE_REUSE, body_path=body.name)

        assert instance.artifact == artifact
        assert instance.cached_response == CR_NGINX
        assert instance.fetch_method == HttpFetchingMethod.FRESH_CACHE_REUSE
        assert instance.filesize == 19225600

        # Make sure our internal filepath links back to the body
        assert os.readlink(instance.filepath) == body.name

        assert instance.is_valid
        assert instance.is_complete
        assert instance.creation_time == 100000.0
        assert instance.completion_time == 23456.0
        assert instance.resume_count == 2.0

        # Ensure that closing an instance makes it invalid
        assert instance.is_valid
        instance.close()
        assert not instance.is_valid


def test_HttpArtifactInstance__resume_then_stale():
    artifact = MagicMock(_is_locked=True)
    name = "Helloworld"
    writer_got_created = False

    def writer_init_mock(*args, **kwargs):
        assert args == tuple()
        assert kwargs == {
            "artifact": artifact,
            "cached_response": CR_NGINX,
            "body_path": instance._HttpArtifactInstance__filepath,
            "name": name
        }

        nonlocal writer_got_created
        writer_got_created = True

    with patch("server.artifact.http.HttpArtifactWriter.__init__", side_effect=writer_init_mock):
        with NamedTemporaryFileWithXAttrRights() as body:
            instance = HttpArtifactInstance(artifact=artifact, cached_response=CR_NGINX,
                                            fetch_method=HttpFetchingMethod.FULL_DOWNLOAD,
                                            body_path=body.name, name=name)

            # Make sure we are starting from the expected state (no STALE attribute)
            assert instance.is_valid
            assert not writer_got_created

            with patch("server.artifact.http.HttpArtifactIO.__init__", return_value=None) as artifactIO_mock:
                polling_delay = 0.001
                instance.open(polling_delay=polling_delay)
                artifactIO_mock.assert_called_once_with(instance=instance,
                                                        bodypath=instance._HttpArtifactInstance__filepath,
                                                        polling_delay=polling_delay)

            # Check for completion, then ensure this triggered the creation of an artifact writer
            assert not instance.is_complete
            assert writer_got_created

            # Mark the artifact as stale
            assert instance.is_valid
            os.setxattr(body.name, XATTR_STALE, b"1")
            assert not instance.is_valid

            # Make sure that calling is_complete again raises StaleHttpArtifactException
            with pytest.raises(StaleHttpArtifactException) as exc:
                instance.is_complete
            assert "The artifact is incomplete and cannot be completed" in str(exc)


# HttpArtifactPruningReport

def test_HttpArtifactPruningReport():
    assert HttpArtifactPruningReport(total_bytes=27262976).total_MiB == 26.0


# HttpArtifact

def test_HttpArtifact__empty_url(tmpdir):
    with pytest.raises(ValueError):
        HttpArtifact(tmpdir, "")


def test_HttpArtifact__integration_test(tmpdir):
    """
    This is likely gonna bite us in the ass, but I would feel much better
    knowing we have a test actually trying to actually download a file than
    just running unit tests.

    That being said, we have unit tests for everything so feel free to disable
    the test if it flakes too much!
    """

    # Skip the test in CI
    if 'CI' in os.environ:
        return  # pragma: nocover

    log_callback = MagicMock()

    url = "https://gitlab.freedesktop.org/gfx-ci/boot2container/-/releases/v0.9.11/downloads/linux-riscv64.dtbs.cpio.xz"
    sha1_digest = "28f8570f8329b643502a176566cf1d8acb10be84"
    artifact1 = HttpArtifact(cache_root=tmpdir, url=url, log_callback=log_callback)
    with artifact1 as instance1:
        # Check the instance1
        filepath = instance1.get_filepath()

        # Validate the location of the body in the cache
        expected_path = f"{tmpdir}/90/d0/71fe69eed73eb313fd3e1a59856e9d1f0fc2be0870fac76969d93a76c315/body"
        assert str(filepath.readlink()) == expected_path

        # Download the file and check its integrity
        data = open(filepath, "rb").read()
        assert sha1(data).hexdigest() == sha1_digest
        assert file_digest(instance1.open(), "sha1").hexdigest() == sha1_digest

        assert instance1.fetch_method == HttpFetchingMethod.FULL_DOWNLOAD
        assert instance1.is_valid

    # Make sure that outside of the `with` section, the instance has become invalid
    assert not instance1.is_valid

    # Store the last access for the file to make sure it gets updated
    last_access_before_refetch = artifact1.last_access

    # Pretend another process opens the same artifact
    artifact2 = HttpArtifact(cache_root=tmpdir, url=url, log_callback=log_callback)
    instance2 = artifact2.get_instance()
    assert instance2.fetch_method == HttpFetchingMethod.FRESH_CACHE_REUSE

    # Make sure that the two artifacts agree on the last access time
    assert artifact1.last_access == artifact2.last_access

    # Make sure that the last access date was updated after the refetch
    assert artifact2.last_access > last_access_before_refetch

    # Make sure no logs were generated
    log_callback.assert_not_called()


@patch("requests.Session")
def test_HttpArtifact__do_get(session_mock):
    url = "https://host.tld/url"
    headers = {"my", "headers"}
    retry = Retry(total=5)

    assert HttpArtifact._do_get(url=url, headers=headers, retry=retry) == session_mock.return_value.get.return_value

    # Make sure the HTTPAdapter was mounted to the session
    calls = session_mock.return_value.mount.call_args_list
    assert len(calls) == 2
    assert calls[0].args[0] == "https://"
    assert calls[0].args[1].max_retries == retry
    assert calls[1].args[0] == "http://"
    assert calls[1].args[1].max_retries == retry

    # Make sure requests was called as expected
    session_mock.return_value.get.assert_called_once_with(url, stream=True, headers=headers,
                                                          allow_redirects=True, timeout=10)


def test_HttpArtifact__get_revalidate_or_reuse_artifact(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")
    request_response = MagicMock(url=artifact.url, history=[], headers=CR_NGINX.headers)

    # Create an empty body
    artifact._HttpArtifact__cached_body_path.touch()

    # Stale HttpArtifacts are not re-used
    artifact._do_get = MagicMock(return_value=request_response)
    with patch.object(HttpArtifactWriter, "get_xattr_as_float", return_value=1.0) as get_xattr_mock:
        cached_response, request, fetching_method = artifact._HttpArtifact__get_revalidate_or_reuse_artifact()
        assert cached_response == CachedResponse.from_request_response(request)
        assert request == artifact._do_get.return_value
        assert fetching_method is None
        artifact._do_get.assert_called_once_with(url=artifact.url, headers={})
        get_xattr_mock.assert_called_once_with(artifact._HttpArtifact__cached_body_path, XATTR_STALE)

    # Check that a cached entry with the wrong URL gets ignored and the response gets overwritten
    cached_response_mock = MagicMock(url="/wrong/url")
    artifact._do_get = MagicMock(return_value=request_response)
    with patch.object(CachedResponse, "from_file", return_value=cached_response_mock) as cr_from_file_mock:
        cached_response, request, fetching_method = artifact._HttpArtifact__get_revalidate_or_reuse_artifact()
        assert cached_response == CachedResponse.from_request_response(request)
        assert request == artifact._do_get.return_value
        assert fetching_method is None
        artifact._do_get.assert_called_once_with(url=artifact.url, headers={})
        cr_from_file_mock.assert_called_once_with(artifact._HttpArtifact__cached_response_path)
        cached_response_mock.update.assert_not_called()
        cached_response_mock.save.assert_not_called()

    # We now have a valid response in cache, pretend we have an active
    # writer and thus we should return directly without revalidation
    with patch.object(HttpArtifactWriter, "has_active_writer", return_value=True) as active_writer_mock:
        cached_response, request, fetching_method = artifact._HttpArtifact__get_revalidate_or_reuse_artifact()
        assert cached_response == CachedResponse.from_request_response(artifact._do_get.return_value)
        assert request is None
        assert fetching_method == HttpFetchingMethod.IN_FLIGHT_REUSE
        artifact._do_get.assert_not_called
        active_writer_mock.assert_called_once_with(artifact._HttpArtifact__cached_body_path)

    # Check that a fresh cached entry gets reused without a request nor changes to the cached value
    cached_response_mock = MagicMock(url=artifact.url, tags=MagicMock(is_fresh=True, can_revalidate=True))
    artifact._do_get = MagicMock(return_value=request_response)
    with patch.object(CachedResponse, "from_file", return_value=cached_response_mock) as cr_from_file_mock:
        cached_response, request, fetching_method = artifact._HttpArtifact__get_revalidate_or_reuse_artifact()
        assert cached_response == cached_response_mock
        assert request is None
        assert fetching_method == HttpFetchingMethod.FRESH_CACHE_REUSE
        artifact._do_get.assert_not_called
        cached_response_mock.save.assert_not_called

    # Check that a stale cache gets revalidated
    cached_response_mock = MagicMock(url=artifact.url, tags=MagicMock(is_fresh=False, can_revalidate=True),
                                     revalidatation_headers=MagicMock(return_value={"reval": "headers"}))
    artifact._do_get = MagicMock(return_value=request_response)
    with patch.object(CachedResponse, "from_file", return_value=cached_response_mock) as cr_from_file_mock:
        cached_response, request, fetching_method = artifact._HttpArtifact__get_revalidate_or_reuse_artifact()
        assert cached_response == cached_response_mock
        assert request == artifact._do_get.return_value
        assert fetching_method is None
        artifact._do_get.assert_called_once_with(url=artifact.url, headers={"reval": "headers"})
        cached_response_mock.update.assert_called_once_with(artifact._do_get.return_value)
        cached_response_mock.save.assert_called_once_with(artifact._HttpArtifact__cached_response_path)

    # Check that a cache entry that isn't fresh nor can be revalidated is overwritten
    cached_response_mock = MagicMock(url=artifact.url, tags=MagicMock(is_fresh=False, can_revalidate=False))
    artifact._do_get = MagicMock(return_value=request_response)
    with patch.object(CachedResponse, "from_file", return_value=cached_response_mock) as cr_from_file_mock:
        cached_response, request, fetching_method = artifact._HttpArtifact__get_revalidate_or_reuse_artifact()
        assert cached_response == CachedResponse.from_request_response(request)
        assert request == artifact._do_get.return_value
        assert fetching_method is None
        artifact._do_get.assert_called_once_with(url=artifact.url, headers={})
        cached_response_mock.update.assert_not_called()
        cached_response_mock.save.assert_not_called()


def test_HttpArtifact_locking_updates_access_time(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")

    # Initial checks
    assert not artifact._is_locked
    assert datetime.now(tz=timezone.utc) - artifact.last_access < timedelta(seconds=5)

    # Lock the artifact and make sure
    access_time = artifact.last_access
    time.sleep(0.01)  # HACK: st_mtime has a resolution of 1us, so make sure we aren't in the same time quanta
    with patch("server.artifact.http.fcntl.flock") as flock_mock:
        artifact._HttpArtifact__lock()
        flock_mock.assert_called_once_with(artifact._HttpArtifact__url_cache_dir_fd, fcntl.LOCK_EX)
    assert artifact._is_locked
    assert artifact.last_access > access_time

    # Make sure the access time does not change when re-locking
    access_time = artifact.last_access
    time.sleep(0.01)  # HACK: st_mtime has a resolution of 1us, so make sure we aren't in the same time quanta
    with patch("server.artifact.http.fcntl.flock") as flock_mock:
        artifact._HttpArtifact__lock()
        flock_mock.assert_not_called()
    assert artifact._is_locked
    assert artifact.last_access == access_time

    # Unlocking releases the lock without affecting the access time
    assert artifact._is_locked
    with patch("server.artifact.http.fcntl.flock") as flock_mock:
        artifact._HttpArtifact__unlock()
        flock_mock.assert_called_once_with(artifact._HttpArtifact__url_cache_dir_fd, fcntl.LOCK_UN)
    assert not artifact._is_locked
    assert artifact.last_access == access_time

    # A second unlock raises an exception without calling flock
    assert not artifact._is_locked
    with patch("server.artifact.http.fcntl.flock") as flock_mock:
        with pytest.raises(AssertionError) as exc:
            artifact._HttpArtifact__unlock()

        assert "Tried to unlock while not being locked" in str(exc)
        flock_mock.assert_not_called()


def store_kwargs_in_mock(*args, **kwargs):
    is_complete_mock = PropertyMock(return_value=True)
    m = MagicMock(args=args, kwargs=kwargs, is_complete_mock=is_complete_mock)
    type(m).is_complete = is_complete_mock
    return m


def test_HttpArtifact__handle_revalidation__check_locking(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")
    exception = ValueError("My error")
    artifact._HttpArtifact__get_revalidate_or_reuse_artifact = MagicMock(side_effect=exception)
    artifact._HttpArtifact__lock = MagicMock()
    artifact._HttpArtifact__unlock = MagicMock()

    # Ensure that we lock the cached entry immediately and release it even
    # when raising an exception
    artifact._HttpArtifact__handle_revalidation()
    assert artifact._HttpArtifact__revalidation_error == exception
    artifact._HttpArtifact__get_revalidate_or_reuse_artifact.assert_called_once_with()
    artifact._HttpArtifact__lock.assert_called_once_with()
    artifact._HttpArtifact__unlock.assert_called_once_with()


def test_HttpArtifact__handle_revalidation__revalidation_already_done(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")
    artifact._HttpArtifact__lock = MagicMock()
    artifact._HttpArtifact__unlock = MagicMock()

    assert not artifact.is_instance_available
    artifact._HttpArtifact__revalidation_done_event.set()
    assert artifact.is_instance_available
    artifact._HttpArtifact__handle_revalidation()

    # Make sure neither the reader nor the writer got created if revalidation had already happened
    assert artifact._HttpArtifact__reader is None
    assert artifact._HttpArtifact__writer is None

    # Make sure we did lock and unlock the artifact while performing the check
    artifact._HttpArtifact__lock.assert_called_once_with()
    artifact._HttpArtifact__unlock.assert_called_once_with()


def test_HttpArtifact__handle_revalidation__reuse_response(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")
    body_path = artifact._HttpArtifact__cached_body_path
    cached_response = MagicMock()

    body_path.touch()
    get_reval_reuse_return = (cached_response, None, HttpFetchingMethod.FRESH_CACHE_REUSE)
    artifact._HttpArtifact__get_revalidate_or_reuse_artifact = MagicMock(return_value=get_reval_reuse_return)
    with patch("server.artifact.http.HttpArtifactWriter.__new__", side_effect=store_kwargs_in_mock):
        with patch("server.artifact.http.HttpArtifactInstance.__new__", side_effect=store_kwargs_in_mock):
            # Check that if the body is incomplete, both the reader and writer are created
            artifact._HttpArtifact__handle_revalidation()
            reader = artifact._HttpArtifact__reader
            writer = artifact._HttpArtifact__writer
            assert artifact._HttpArtifact__revalidation_error is None
            assert reader.args == (HttpArtifactInstance,)
            assert reader.kwargs == {"artifact": artifact, "cached_response": cached_response,
                                     "fetch_method": HttpFetchingMethod.FRESH_CACHE_REUSE,
                                     "body_path": body_path, "name": artifact.name}
            assert writer is None

            # Make sure we restarted the download if incomplete
            reader.is_complete_mock.assert_called_once_with()


def handle_revalidation__new_request_made(tmpdir, status_code, cached_response=MagicMock()):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")
    request = MagicMock(status_code=status_code)

    artifact._HttpArtifact__cached_body_path.touch()
    get_reval_reuse_return = (cached_response, request, None)
    artifact._HttpArtifact__get_revalidate_or_reuse_artifact = MagicMock(return_value=get_reval_reuse_return)
    with patch("server.artifact.http.HttpArtifactWriter.__new__", side_effect=store_kwargs_in_mock):
        with patch("server.artifact.http.HttpArtifactInstance.__new__", side_effect=store_kwargs_in_mock):
            artifact._HttpArtifact__handle_revalidation()

            return artifact, cached_response, request


def test_HttpArtifact__handle_revalidation__new_request_made__success(tmpdir):
    artifact, cached_response, request = handle_revalidation__new_request_made(tmpdir, 200)

    body_path = artifact._HttpArtifact__cached_body_path
    reader = artifact._HttpArtifact__reader
    writer = artifact._HttpArtifact__writer
    assert artifact._HttpArtifact__revalidation_error is None
    assert reader.args == (HttpArtifactInstance,)
    assert reader.kwargs == {"artifact": artifact, "cached_response": cached_response,
                             "fetch_method": HttpFetchingMethod.FULL_DOWNLOAD,
                             "body_path": body_path, "name": artifact.name}
    assert writer.args == (HttpArtifactWriter,)
    assert writer.kwargs == {"artifact": artifact, "cached_response": cached_response,
                             "body_path": body_path, "name": artifact.name,
                             "request": request}
    request.close.assert_not_called()


def test_HttpArtifact__handle_revalidation__new_request_made__revalidated(tmpdir):
    artifact, cached_response, request = handle_revalidation__new_request_made(tmpdir, 304)

    body_path = artifact._HttpArtifact__cached_body_path
    reader = artifact._HttpArtifact__reader
    assert artifact._HttpArtifact__revalidation_error is None
    assert reader.args == (HttpArtifactInstance,)
    assert reader.kwargs == {"artifact": artifact, "cached_response": cached_response,
                             "fetch_method": HttpFetchingMethod.REUSE_AFTER_REVALIDATION,
                             "body_path": body_path, "name": artifact.name}
    assert artifact._HttpArtifact__writer is None
    request.close.assert_called_once_with()


def test_HttpArtifact__handle_revalidation__new_request_made__missing(tmpdir):
    artifact, cached_response, request = handle_revalidation__new_request_made(tmpdir, 404)

    assert "Failed to access the artifact - Got status 404" in str(artifact._HttpArtifact__revalidation_error)
    assert artifact._HttpArtifact__reader is None
    assert artifact._HttpArtifact__writer is None
    request.close.assert_called_once_with()


def test_HttpArtifact__handle_revalidation__new_request_made__reuse_on_error(tmpdir):
    cached_response = MagicMock(tags=CacheState.REUSE_ON_ERROR)

    # Incomplete artifact do not lead to re-use
    artifact, cached_response, request = handle_revalidation__new_request_made(tmpdir, 500,
                                                                               cached_response=cached_response)
    assert "Failed to access the artifact - Got status 500" in str(artifact._HttpArtifact__revalidation_error)
    request.close.assert_called_once_with()

    # Complete artifact but wrong status code
    with patch("server.artifact.http.HttpArtifactWriter.get_xattr_as_float", return_value=1.0):
        artifact, cached_response, request = handle_revalidation__new_request_made(tmpdir, 404,
                                                                                   cached_response=cached_response)
    assert "Failed to access the artifact - Got status 404" in str(artifact._HttpArtifact__revalidation_error)
    request.close.assert_called_once_with()

    # Complete artifact and right status code lead to re-use
    with patch("server.artifact.http.HttpArtifactWriter.get_xattr_as_float", return_value=1.0):
        artifact, cached_response, request = handle_revalidation__new_request_made(tmpdir, 500,
                                                                                   cached_response=cached_response)
    body_path = artifact._HttpArtifact__cached_body_path
    reader = artifact._HttpArtifact__reader
    assert artifact._HttpArtifact__revalidation_error is None
    assert reader.args == (HttpArtifactInstance,)
    assert reader.kwargs == {"artifact": artifact, "cached_response": cached_response,
                             "fetch_method": HttpFetchingMethod.REUSE_DUE_TO_ERROR,
                             "body_path": body_path, "name": artifact.name}
    assert artifact._HttpArtifact__writer is None
    request.close.assert_called_once_with()


def test_HttpArtifact__background_revalidation(tmpdir):
    # Make sure that setting the `start_bg_validation` parameter calls start_background_revalidation()
    with patch("server.artifact.http.HttpArtifact.start_background_revalidation") as bg_reval_mock:
        HttpArtifact(cache_root=tmpdir, url="https://host.tld/path", start_bg_validation=True)
        bg_reval_mock.assert_called_with()

    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")
    artifact._HttpArtifact__handle_revalidation = MagicMock()

    # Make sure we do not start the revalidation thread if it already happened
    artifact._HttpArtifact__revalidation_done_event.set()
    artifact.start_background_revalidation()
    artifact._HttpArtifact__handle_revalidation.assert_not_called()

    # Ensure the revalidation thread gets kicked off if revalidation did not happen
    artifact._HttpArtifact__revalidation_done_event.clear()
    artifact.start_background_revalidation()
    artifact._HttpArtifact__handle_revalidation.assert_called_once_with()


def test_HttpArtifact__enter_exit(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")

    # Make sure the reader is closed and the writer got a chance to finish before returning
    artifact._HttpArtifact__reader = reader = MagicMock()
    artifact._HttpArtifact__writer = writer = MagicMock()
    artifact._HttpArtifact__revalidation_done_event.set()
    with artifact as instance:
        assert instance == reader
        reader.close.assert_not_called()
        writer.join.assert_not_called()
    reader.close.assert_called_once_with()
    writer.join.assert_called_once_with()


def test_HttpArtifact__get_instance(tmpdir):
    artifact = HttpArtifact(cache_root=tmpdir, url="https://host.tld/path")

    # No errors
    artifact._HttpArtifact__reader = reader = MagicMock()
    artifact._HttpArtifact__revalidation_done_event.set()
    assert artifact.get_instance() == reader

    # Errors are re-raised
    exception = ValueError("My error")
    artifact._HttpArtifact__revalidation_error = exception
    with pytest.raises(ValueError) as exc:
        artifact.get_instance()
    assert str(exception) in str(exc)


# HttpArtifactCache


@patch("server.artifact.http.HttpArtifact")
def test_HttpArtifactCache__get_or_reuse_instance(http_artifact_mock, tmpdir):
    log_callback = MagicMock()
    cache = HttpArtifactCache(cache_root=tmpdir, log_callback=log_callback)

    url = "https://gitlab.freedesktop.org/"

    # Open an artifact, while pretending it is not currently available
    http_artifact_mock.return_value.is_instance_available = False
    instance = cache.get_or_reuse_instance(url=url, name="MockArtifact")

    # Make sure we got a message that the artifact needed revalidation
    msg = 'Waiting for [MockArtifact](https://gitlab.freedesktop.org/) to finish revalidation'
    log_callback.assert_called_once_with(msg)

    # Ensure we get the same instance when we asked again
    http_artifact_mock.return_value.is_instance_available = True
    assert instance == cache.get_or_reuse_instance(url=url, name="MockArtifact")
    assert http_artifact_mock.call_count == 1
    assert log_callback.call_count == 1

    # Make sure the instance is re-created if marked as invalid
    instance.is_valid = False
    cache.get_or_reuse_instance(url=url, name="MockArtifact")
    assert http_artifact_mock.call_count == 2


def test_HttpArtifactCache__prune_artifacts(tmpdir):
    CR_GITLAB.save(HttpArtifact(cache_root=tmpdir, url="/url1")._HttpArtifact__cached_response_path)
    CR_NGINX.save(HttpArtifact(cache_root=tmpdir, url="/url2")._HttpArtifact__cached_response_path)

    log_callback = MagicMock()

    cache = HttpArtifactCache(cache_root=tmpdir, log_callback=log_callback)

    # Make sure that no artifacts get deleted if unused_for is in the future
    with patch("server.artifact.http.shutil.rmtree") as rmtree_mock:
        report = cache.prune_artifacts(unused_for=timedelta(minutes=1))
        assert report.found == 2
        assert report.pruned == 0
        assert report.error == 0
        assert report.total_bytes == 0
        assert report.total_seconds > 0
        rmtree_mock.assert_not_called()
        assert log_callback.call_count == 0

    # Make sure that all artifacts get deleted if unused_for is in the past
    with patch("server.artifact.http.shutil.rmtree") as rmtree_mock:
        report = cache.prune_artifacts(unused_for=timedelta(minutes=-1))
        assert report.found == 2
        assert report.pruned == 2
        assert report.error == 0
        assert report.total_bytes == 1359
        rmtree_mock.assert_has_calls(any_order=True, calls=[
            call(f"{tmpdir}/f5/13/8edd0e454a2f3382264ebea30a59a67e7f1102faec98cc9e0f921f7ba20c"),
            call(f"{tmpdir}/42/7b/f70c9c1032f709a7d9a2f0a95f9c38145dec2be283d059f97d611ae947e5")],)
        assert log_callback.call_count == 0

    # Make sure that any error happening during deletion get counted as an error
    with patch("server.artifact.http.shutil.rmtree", side_effect=ValueError) as rmtree_mock:
        report = cache.prune_artifacts(unused_for=timedelta(minutes=-1))
        assert report.found == 2
        assert report.pruned == 0
        assert report.error == 2
        assert report.total_bytes == 0
        assert log_callback.call_count == 2

    # Make sure a missing folder won't result in an exception being thrown
    HttpArtifactCache(cache_root="/path/that/doesnt/exist", log_callback=log_callback).prune_artifacts()
    assert log_callback.call_count == 3
