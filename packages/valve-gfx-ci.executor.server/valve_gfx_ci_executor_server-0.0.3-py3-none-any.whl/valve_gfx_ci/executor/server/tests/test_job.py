from datetime import datetime, timedelta
from freezegun import freeze_time
from jinja2.exceptions import TemplateSyntaxError
from unittest import mock
from unittest.mock import patch, MagicMock
import os
import re

import pytest
from pydantic import ValidationError

import server
from server.artifact.uimage import UImageFormatCompression, UImageFormatOS, UImageFormatType
from server.artifact.archive import ArchiveFormat, ArchiveCompression, ArtifactKeep, ArtifactAdd
from server.artifact import DataArtifact
from server.dhcpd import MacAddress, CPUArch
from server.job import Target, Timeout, Timeouts, ConsoleState, Job, Pattern, CollectionOfLists
from server.job import Watchdog, KernelDeployment, DeploymentState, FastbootDeployment
from server.job import ArtifactDeployment, StorageArtifactDeployment, DhcpRequestMatcher, DhcpDeployment
from server.job import (
    ensure_is_valid_host_port,
    ensure_is_valid_regex,
    compile_re,
    ArtifactFormatDeployment,
    UBootArtifactFormatDeployment,
)
from server.job import ArtifactArchiveFormatDeployment, ArtifactArchiveFormatKeep, assert_is_valid_imagestore_name
from server.job import assert_is_valid_image_name, ImageStoreStorage, ContainerImageStorage, StorageDeployment
from server.job import assert_is_valid_resource_name, Deployment, convert_human_size_to_bytes, NbdStorage
from server.job import ArtifactArchiveAddArtifact
from server.imagestore import ImageStoreImage, ImageStorePullPolicy
from server.nbd import Nbd
import server.config as config

# Target


def test_Target_from_job__no_id_nor_tags():
    with pytest.raises(ValueError) as exc:
        Target()

    msg = "The target is neither identified by tags or id. Use empty tags to mean 'any machines'."
    assert msg in str(exc.value)


def test_Target_from_job__id_only():
    target_job = {
        "id": "MyID",
    }

    target = Target(**target_job)
    assert target.id == target_job['id']
    assert target.tags == []
    assert str(target) == f"<Target: id={target.id}, tags={target.tags}>"


def test_Target_from_job__tags_only():
    target_job = {
        "tags": ['tag 1', 'tag 2']
    }

    target = Target(**target_job)
    assert target.id is None
    assert target.tags == target_job['tags']
    assert str(target) == f"<Target: id={target.id}, tags={target.tags}>"


def test_Target_from_job__both_id_and_tags():
    target_job = {
        "id": "MyID",
        "tags": ['tag 1', 'tag 2']
    }

    target = Target(**target_job)
    assert target.id == target_job['id']
    assert target.tags == target_job['tags']
    assert str(target) == f"<Target: id={target.id}, tags={target.tags}>"


# Timeout


def test_Timeout__expiration_test():
    start_time = datetime(2021, 1, 1, 12, 0, 0)
    with freeze_time(start_time.isoformat()):
        timeout = Timeout(minutes=1, retries=0)
        assert timeout.started_at is None
        assert not timeout.is_started
        assert timeout.active_for is None
        assert timeout.remaining_time == timeout.timeout

        # Start the timeout and check the state
        timeout.start()
        assert timeout.started_at == start_time
        assert timeout.is_started
        assert timeout.active_for == timedelta()
        assert not timeout.has_expired
        assert timeout.remaining_time == timeout.timeout

        # Go right to the limit of the timeout
        delta = timedelta(seconds=60)
        with freeze_time((start_time + delta).isoformat()):
            assert timeout.started_at == start_time
            assert timeout.active_for == delta
            assert timeout.is_started
            assert not timeout.has_expired
            assert timeout.remaining_time == timedelta()

        # And check that an extra millisecond trip it
        delta = timedelta(seconds=60, milliseconds=1)
        with freeze_time((start_time + delta).isoformat()):
            assert timeout.started_at == start_time
            assert timeout.active_for == delta
            assert timeout.is_started
            assert timeout.has_expired
            assert timeout.remaining_time < timedelta()

        # Stop the timeout and check the state
        timeout.stop()
        assert timeout.started_at is None
        assert not timeout.is_started
        assert timeout.active_for is None
        assert timeout.remaining_time == timeout.timeout


def test_Timeout__retry_lifecycle():
    timeout = Timeout(seconds=42, retries=1)

    # Check the default state
    assert timeout.started_at is None
    assert timeout.active_for is None
    assert timeout.retried == 0

    # Start the timeout
    start_time = datetime(2021, 1, 1, 12, 0, 0)
    with freeze_time(start_time.isoformat()):
        timeout.start()
        assert timeout.started_at == start_time
        assert timeout.retried == 0
        assert timeout.active_for == timedelta()
        assert not timeout.has_expired

    # Check that the default reset sets started_at to now()
    start_time = datetime(2021, 1, 1, 12, 0, 1)
    with freeze_time(start_time.isoformat()):
        timeout.reset()
        assert timeout.started_at == start_time

        # Check that a resetting to a certain time does as it should
        new_start = start_time - timedelta(seconds=1)
        timeout.reset(new_start)
        assert timeout.started_at == new_start

    # Do the first retry
    assert timeout.retry()
    assert timeout.started_at is None
    assert timeout.retried == 1

    # Second retry should fail
    assert not timeout.retry()


def test_Timeout_from_job():
    fields = {"days": 5, "hours": 6, "minutes": 7, "seconds": 8, "milliseconds": 9}

    delay = timedelta(**fields)
    timeout = Timeout(retries=42, **fields)
    timeout.name = "Yeeepeee"

    assert timeout.timeout == delay
    assert timeout.retries == 42
    assert str(timeout) == f"<Timeout Yeeepeee: value={delay}, retries=0/42>"


# Timeouts


def test_Timeouts__overall_with_retries():
    for t_type in ["overall", "infra_teardown"]:
        with pytest.raises(ValueError) as exc:
            Timeouts(**{t_type: Timeout(retries=1)})
        assert "Neither the overall nor the teardown timeout can have retries" in str(exc.value)


def test_Timeouts__default():
    timeouts = Timeouts()

    for timeout in timeouts:
        if timeout.name not in ["overall", "infra_setup", "infra_teardown"]:
            assert timeout.timeout == timedelta.max
            assert timeout.retries == 0

    assert timeouts.overall.timeout == timedelta(hours=6)
    assert timeouts.infra_setup.timeout == timedelta(hours=1.5)
    assert timeouts.infra_teardown.timeout == timedelta(hours=1.5)

    assert timeouts.expired_list == []
    assert not timeouts.has_expired
    assert timeouts.watchdogs == {}


def test_Timeouts__expired():
    overall = Timeout(days=1, retries=0)
    boot_cycle = Timeout(seconds=0, retries=0)
    wd1 = Timeout(seconds=0, retries=0)

    overall.start()
    boot_cycle.start()

    timeouts = Timeouts(overall=overall, boot_cycle=boot_cycle, watchdogs={"wd1": wd1})
    assert timeouts.has_expired
    assert timeouts.expired_list == [boot_cycle]

    boot_cycle.stop()
    assert not timeouts.has_expired
    assert timeouts.expired_list == []

    wd1.start()
    assert timeouts.has_expired
    assert timeouts.expired_list == [wd1]


def test_Timeouts__from_job():
    job_timeouts = {
        "first_console_activity": {
            "seconds": 45
        },
        "console_activity": {
            "seconds": 13
        },
        "watchdogs": {
            "custom1": {
                "seconds": 42
            }
        }
    }

    timeouts = Timeouts(**job_timeouts)

    assert timeouts.first_console_activity.timeout == timedelta(seconds=45)
    assert timeouts.console_activity.timeout == timedelta(seconds=13)
    assert timeouts.watchdogs.get("custom1").timeout == timedelta(seconds=42)
    assert timeouts.watchdogs["custom1"] in timeouts


# Pattern


def test_Pattern():
    pattern = Pattern(regex="Helloworld")

    assert str(pattern) == "b'Helloworld'"


def test_Pattern_from_job__invalid_regex():
    with pytest.raises(ValueError) as excinfo:
        Pattern(**{"regex": "BOOM\\"})

    error_msg = "Console pattern 'BOOM\\' is not a valid regular expression: bad escape (end of pattern)"
    assert error_msg in str(excinfo.value)


# Watchdogs


def test_Watchdog__process_line():
    wd = Watchdog(**{
        "start": {"regex": "start"},
        "reset": {"regex": "reset"},
        "stop": {"regex": "stop"},
    })

    # Check that nothing explodes if we have no timeouts set
    assert wd.process_line(b"line") == {}

    # Set the timeout
    wd.set_timeout(MagicMock(is_started=False))
    wd.timeout.start.assert_not_called()
    wd.timeout.reset.assert_not_called()
    wd.timeout.stop.assert_not_called()

    # Check that sending the reset/stop patterns before starting does nothing
    assert wd.process_line(b"line reset line") == {}
    assert wd.process_line(b"line stop line") == {}
    wd.timeout.start.assert_not_called()
    wd.timeout.reset.assert_not_called()
    wd.timeout.stop.assert_not_called()

    # Check that the start pattern starts the timeout
    assert wd.process_line(b"line start line") == {"start"}
    wd.timeout.start.assert_called_once()
    wd.timeout.reset.assert_not_called()
    wd.timeout.stop.assert_not_called()

    # Emulate the behaviour of the timeout
    wd.timeout.is_started = True

    # Check that the start pattern does not restart the timeout
    assert wd.process_line(b"line start line") == {}
    wd.timeout.start.assert_called_once()
    wd.timeout.reset.assert_not_called()
    wd.timeout.stop.assert_not_called()

    # Check that the reset pattern works
    assert wd.process_line(b"line reset line") == {"reset"}
    wd.timeout.start.assert_called_once()
    wd.timeout.reset.assert_called_once()
    wd.timeout.stop.assert_not_called()

    # Check that the stop pattern works
    assert wd.process_line(b"line stop line") == {"stop"}
    wd.timeout.start.assert_called_once()
    wd.timeout.reset.assert_called_once()
    wd.timeout.stop.assert_called_once()


def test_Watchdog__stop():
    wd = Watchdog(**{
        "start": {"regex": "start"},
        "reset": {"regex": "reset"},
        "stop": {"regex": "stop"},
    })

    # Check that nothing explodes if we have no timeouts set
    wd.cancel()

    # Set the timeout
    wd.set_timeout(MagicMock(is_started=False))
    wd.timeout.stop.assert_not_called()

    # Check that sending the reset/stop patterns before starting does nothing
    wd.cancel()
    wd.timeout.stop.assert_called_once()


# ConsoleState


def test_ConsoleState__missing_session_end():
    with pytest.raises(ValidationError):
        ConsoleState(session_end=None, session_reboot=None, job_success=None, job_warn=None,
                     machine_unfit_for_service=None)


def test_ConsoleState__simple_lifecycle():
    state = ConsoleState(session_end=Pattern("session_end"), session_reboot=None, job_success=None, job_warn=None,
                         machine_unfit_for_service=None)

    assert state.job_status == "INCOMPLETE"
    assert not state.session_has_ended
    assert not state.needs_reboot

    state.process_line(b"oh oh oh")
    assert state.job_status == "INCOMPLETE"
    assert not state.session_has_ended
    assert not state.needs_reboot

    state.process_line(b"blabla session_end blaba\n")
    assert state.job_status == "COMPLETE"
    assert state.session_has_ended
    assert not state.needs_reboot


def test_ConsoleState__lifecycle_with_extended_support():
    state = ConsoleState(session_end=Pattern("session_end"), session_reboot=Pattern("session_reboot"),
                         job_success=Pattern("job_success"), job_warn=Pattern("job_warn"),
                         machine_unfit_for_service=Pattern("machine_unfit_for_service"),
                         watchdogs={"wd1": Watchdog(start=Pattern(r"wd1_start"),
                                                    reset=Pattern(r"wd1_reset"),
                                                    stop=Pattern(r"wd1_stop"))})

    assert state.job_status == "INCOMPLETE"
    assert not state.session_has_ended
    assert not state.needs_reboot
    assert not state.machine_is_unfit_for_service

    assert state.process_line(b"oh oh oh") == set()
    assert state.job_status == "INCOMPLETE"
    assert not state.session_has_ended
    assert not state.needs_reboot
    assert not state.machine_is_unfit_for_service

    assert state.process_line(b"blabla session_reboot blabla") == {"session_reboot"}
    assert state.job_status == "INCOMPLETE"
    assert not state.session_has_ended
    assert state.needs_reboot
    assert not state.machine_is_unfit_for_service

    state.reset_per_boot_state()
    assert not state.session_has_ended
    assert not state.needs_reboot

    assert state.process_line(b"blabla session_end blaba\n") == {"session_end"}
    assert state.job_status == "FAIL"
    assert state.session_has_ended
    assert not state.needs_reboot
    assert not state.machine_is_unfit_for_service

    assert state.process_line(b"blabla job_success blaba\n") == {"job_success"}
    assert state.job_status == "PASS"
    assert state.session_has_ended
    assert not state.needs_reboot
    assert not state.machine_is_unfit_for_service

    assert state.process_line(b"blabla job_warn blaba\n") == {"job_warn"}
    assert state.job_status == "WARN"
    assert state.session_has_ended
    assert not state.needs_reboot
    assert not state.machine_is_unfit_for_service

    assert state.process_line(b"blabla machine_unfit_for_service blaba\n") == {"machine_unfit_for_service"}
    assert state.job_status == "WARN"
    assert state.session_has_ended
    assert not state.needs_reboot
    assert state.machine_is_unfit_for_service

    state.watchdogs.get("wd1").set_timeout(Timeout.create(name="wd1", seconds=1, retries=1))
    assert state.process_line(b"blabla wd1_start blaba\n") == {"wd1.start"}
    assert state.job_status == "WARN"
    assert state.session_has_ended
    assert not state.needs_reboot
    assert state.machine_is_unfit_for_service


def test_ConsoleState__default():
    console_state = ConsoleState()

    print(console_state.session_end.regex.pattern)
    assert console_state.session_end.regex.pattern == b"^\\[[\\d \\.]{12}\\] reboot: Power Down$"
    assert console_state.session_reboot is None
    assert console_state.job_success is None
    assert console_state.job_warn is None
    assert console_state.machine_unfit_for_service is None

    config.CONSOLE_PATTERN_DEFAULT_MACHINE_UNFIT_FOR_SERVICE_REGEX = "TEST"
    console_state = ConsoleState()
    assert console_state.machine_unfit_for_service.regex.pattern == b"TEST"


def test_ConsoleState_from_job__full():
    console_state = ConsoleState(**{
        "session_end": {
            "regex": "session_end"
        }, "session_reboot": {
            "regex": "session_reboot"
        }, "job_success": {
            "regex": "job_success"
        }, "job_warn": {
            "regex": "job_warn"
        }, "machine_unfit_for_service": {
            "regex": "unfit_for_service"
        }, "watchdogs": {
            "mywatchdog": {
                "start": {"regex": "start"},
                "reset": {"regex": "reset"},
                "stop": {"regex": "stop"},
            }
        }
    })

    assert console_state.session_end.regex.pattern == b"session_end"
    assert console_state.session_reboot.regex.pattern == b"session_reboot"
    assert console_state.job_success.regex.pattern == b"job_success"
    assert console_state.job_warn.regex.pattern == b"job_warn"
    assert console_state.machine_unfit_for_service.regex.pattern == b"unfit_for_service"


# CollectionOfLists


def test_CollectionOfLists__invalid_collection_name():
    # Can't use a keyword as category
    with pytest.raises(ValidationError):
        CollectionOfLists[str]({":uncategorised": ["Hello"]})


def test_CollectionOfLists__None_lists():
    cl = CollectionOfLists[str](categories={"01-cat1": None}, uncategorised=None)
    assert cl.uncategorised == []
    assert cl.as_list == []
    assert list(cl) == cl.as_list


def test_CollectionOfLists__from_job():
    # CollectionOfLists
    val = CollectionOfLists[str]()
    assert CollectionOfLists[str].from_job(val) == val

    # Single value
    assert CollectionOfLists[str].from_job("hello").as_list == ["hello"]

    # List of values
    assert CollectionOfLists[int].from_job([1, 2]).as_list == [1, 2]

    # Categories
    cl = CollectionOfLists[str].from_job({"01-cat1": "Neo!",
                                          "00-cat2": ["Wake", "up,"],
                                          ":uncategorised": ["Don't", "be", "lazy!"]})
    assert cl.uncategorised == ["Don't", "be", "lazy!"]
    assert cl.as_list == ["Wake", "up,", "Neo!", "Don't", "be", "lazy!"]
    assert list(cl) == cl.as_list
    assert cl[2] == "Neo!"

    # Invalid collection name
    with pytest.raises(ValidationError):
        CollectionOfLists[str].from_job({":cat": ["Hello"]})


def test_CollectionOfLists__str():
    assert str(CollectionOfLists[str](uncategorised=["Wake", "up,", "Neo!"])) == "Wake up, Neo!"


def test_CollectionOfLists__equality():
    categories = {
        "cat1": ["Hello"],
        "cat2": ["World"]
    }
    uncategorised = ["Wake", "up,", "Neo!"]

    # Make sure that 2 objects constructed with the same values are equal
    assert CollectionOfLists[str](categories, uncategorised) == CollectionOfLists[str](categories, uncategorised)

    # Make sure all combinaisons of missing inputs don't result in a match
    assert CollectionOfLists[str](categories) != CollectionOfLists[str](categories, uncategorised)
    assert CollectionOfLists[str](uncategorised=uncategorised) != CollectionOfLists[str](categories, uncategorised)
    assert CollectionOfLists[str](categories, uncategorised) != CollectionOfLists[str](categories)
    assert CollectionOfLists[str](categories, uncategorised) != CollectionOfLists[str](uncategorised=uncategorised)

    # Comparison to a string
    assert CollectionOfLists[str](categories, uncategorised) == "Hello World Wake up, Neo!"


def test_CollectionOfLists__update():
    categories = {
        "greeting": ["Hello"],
        "who": ["World"],
    }
    uncategorised = ["and", "the", "universe!"]

    c = CollectionOfLists[str](categories=categories, uncategorised=uncategorised)
    assert c == "Hello World and the universe!"

    # Replacing a category also keeps the uncategorised
    assert c.update(CollectionOfLists[str](categories={"greeting": ["Bye Bye"]})) == c
    assert c == "Bye Bye World and the universe!"

    # Get rid of a complete category, add another one, and replace the uncategorised list
    c.update(CollectionOfLists[str](categories={"greeting": ["Welcome"], "who": []},
                                    uncategorised=["my", "son", "to", "the", "machine"]))
    assert c == "Welcome my son to the machine"


def test_CollectionOfLists__artifacts():
    artifact = ArtifactDeployment(url="https://host.tld/url1")
    artifact_none = ArtifactDeployment()

    c = CollectionOfLists[ArtifactDeployment](uncategorised=[artifact, artifact_none])
    assert c.artifacts == {
        "https://host.tld/url1": {("0", ): artifact},
        None: {("1", ): artifact_none},
    }


# Regex

def test_Regex():
    assert compile_re("HelloWorld") == re.compile("HelloWorld")

    with pytest.raises(ValueError):
        compile_re("*Helloworld*")


def test_RegexAsStr():
    assert ensure_is_valid_regex("HelloWorld") == "HelloWorld"

    with pytest.raises(ValueError):
        ensure_is_valid_regex("*Helloworld*")


# NetworkEndpoint

@pytest.mark.parametrize(
    "host_port",
    [
        "host:123",
        "f.q.d.n:123",
        "127.0.0.1:123",
        "[::1]:123",
    ],
)
def test_NetworkEndpoint_valid(host_port):
    assert ensure_is_valid_host_port(host_port)


@pytest.mark.parametrize(
    "host_port",
    [
        "host",
        "host:port",
        "host:-1",
        "host:0",
        "host:100000",
        "[::1]",
        "::1",
        "::1]:1",
        "[::1:1",
    ],
)
def test_NetworkEndpoint_invalid(host_port):
    with pytest.raises(ValueError):
        ensure_is_valid_host_port(host_port)


# Deployment


def test_ArtifactDeployment__invalid_url():
    with pytest.raises(ValueError) as exc:
        ArtifactDeployment(url="ftp://invalid/url")
    assert "Unsupported schema" in str(exc.value) or "URL scheme should be 'http' or 'https'" in str(exc.value)


def test_ArtifactDeployment__malformed_url():
    with pytest.raises(ValueError) as exc:
        ArtifactDeployment(url=r"http://invalid\url")
    assert "The URL is malformed" in str(exc.value)


def test_KernelDeployment_cmdline():
    assert KernelDeployment(cmdline="toto").cmdline == "toto"
    assert KernelDeployment(cmdline=["tag1", "tag2"]).cmdline == "tag1 tag2"
    assert KernelDeployment().cmdline is None


def test_StorageArtifactDeployment__sources_are_exclusive():
    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(path="/path", url="https://host.tld/", data="helloworld")
    assert "Can only set one artifact source: 'archive', 'data', or 'url'" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(path="/path", url="https://host.tld/", archive={"extension": "cpio"})
    assert "Can only set one artifact source: 'archive', 'data', or 'url'" in str(exc.value)


def test_StorageArtifactDeployment__path_missing():
    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(url="https://host.tld/")
    assert "Cannot be empty" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(path="", url="https://host.tld/")
    assert "Cannot be empty" in str(exc.value)


def test_StorageArtifactDeployment__path_not_absolute():
    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(path="hello", url="https://host.tld/")
    assert "Needs to be absolute" in str(exc.value)


def test_StorageArtifactDeployment__reserved_path():
    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(path="/_/blabla", url="https://host.tld/")
    assert "Reserved path" in str(exc.value)


def test_StorageArtifactDeployment__fixed_url():
    artifact = StorageArtifactDeployment(path="/hello/world", url="https://host.tld/blabla")

    assert not artifact.has_dynamic_url
    assert not artifact.matches("/other")
    assert artifact.matches("/hello/world")


def test_StorageArtifactDeployment__matches__regex():
    artifact = StorageArtifactDeployment(path="/(hello|goodbye)/world", url=r"https://host.tld/\1")

    assert artifact.has_dynamic_url
    assert not artifact.matches("/hi/world")
    assert artifact.matches("/(hello|goodbye)/world")  # Literal matches win
    assert artifact.matches("/hello/world").groups() == ("hello", )
    assert artifact.matches("/goodbye/world").groups() == ("goodbye", )


def test_StorageArtifactDeployment__open_with_rewritten_url():
    def check(path, expected_url):
        artifact_cache = MagicMock()
        artifact.open(path, artifact_cache=artifact_cache)
        artifact_cache.get_or_reuse_instance.assert_called_once_with(url=expected_url, name=path)

    artifact = StorageArtifactDeployment(path="/(hello|goodbye)/world", url=r"https://host.tld/\1")

    assert artifact.has_dynamic_url

    # Literal matches and non-matches return the literal URL
    check("/(hello|goodbye)/world", r"https://host.tld/\1")
    check("/hi/world", r"https://host.tld/\1")

    # Regular expression matching
    for greeting in ["hello", "goodbye"]:
        check(f"/{greeting}/world", f"https://host.tld/{greeting}")


def test_StorageArtifactDeployment__invalid_rewritten_url():
    with pytest.raises(ValueError) as exc:
        StorageArtifactDeployment(path="/(hello|goodbye)/world", url=r"https://host.tld/\1\2\3")
    assert "The `url` parameter is neither a valid" in str(exc)


def test_FastbootDeployment():
    assert str(FastbootDeployment()) == "<Fastboot: >"

    fb = str(FastbootDeployment(header_version=4, dtb_offset=0x123456))
    assert fb == "<Fastboot: header_version=4, dtb_offset=0x123456>"


@pytest.mark.parametrize(
    "data, rendered, exception",
    [
        ("#!jinja2\n", "", None),
        ("#!jinja2\n{{ toto", None, TemplateSyntaxError),
        ("#!jinja2\ntoto }}", "toto }}", None),
        ("#!jinja2\n{{ toto }}", "tata", None),
        ("#!jinja2\n{{ unset_var }}", "", None),
    ],
)
def test_ArtifactDeployment__render_data_explicit_template(data, rendered, exception):
    if exception is None:
        with patch.dict(os.environ, {"EXECUTOR_JOB__TOTO": "tata"}):
            assert ArtifactDeployment.render_data_template(None, data) == rendered
    else:
        assert rendered is None
        with pytest.raises(exception):
            ArtifactDeployment.render_data_template(None, data)


def test_ArtifactDeployment__render_data_template():
    assert ArtifactDeployment.render_data_template(None, b"{{ toto }}") == b"{{ toto }}"


def test_ArtifactDeployment__open__data__valid_template():
    artifact = ArtifactDeployment(data="hello {{ tmpl_example }}")

    os.environ['EXECUTOR_JOB__TMPL_EXAMPLE'] = 'world'
    f = artifact.open("/path")
    del os.environ['EXECUTOR_JOB__TMPL_EXAMPLE']

    assert f.content_type == "text/plain;charset=UTF-8"
    assert f.read() == "hello world".encode()


def test_ArtifactDeployment__open__data__invalid_template():
    artifact = ArtifactDeployment(data="hello {{ toto")
    f = artifact.open("/path")
    assert f.read() == artifact.data.encode()


def test_ArtifactDeployment__open__url():
    url = "http://my/url"
    artifact = ArtifactDeployment(url=url)

    artifact_cache = MagicMock()
    polling_delay = 1
    f = artifact.open("/path", polling_delay=polling_delay, artifact_cache=artifact_cache)

    assert f == artifact_cache.get_or_reuse_instance.return_value.open.return_value
    artifact_cache.get_or_reuse_instance.assert_called_once_with(url=url, name="/path")
    artifact_cache.get_or_reuse_instance.return_value.open.assert_called_once_with(polling_delay=polling_delay)


def test_ArtifactDeployment__open__data_with_formated_data():
    artifact = ArtifactDeployment(data="helloworld",
                                  format=[ArtifactFormatDeployment(uboot=UBootArtifactFormatDeployment())])

    start_time = datetime(2024, 9, 23, 12, 0, 0)
    with freeze_time(start_time.isoformat()):
        f = artifact.open("/path")

    assert f.content_type == "application/x.uimage"
    assert f.etag == "b2c77802654ac120cada80764fd36277"


def test_ArtifactDeployment__open__archive():
    artifact = ArtifactDeployment(archive={"extension": "cpio"})

    f = artifact.open("/module.cpio")

    assert f.content_type == "application/octet-stream"
    assert f.etag == "cae66941d9efbd404e4d88758ea67670"


def test_is_valid_image_name():
    assert assert_is_valid_image_name("alpine")
    assert assert_is_valid_image_name("alpine:latest")
    assert assert_is_valid_image_name("registry.freedesktop.org/gfx-ci/ci-tron/machine-registration:latest")
    assert assert_is_valid_image_name("docker://registry.freedesktop.org/gfx-ci/ci-tron/machine-registration:latest")

    with pytest.raises(ValueError) as exc:
        assert_is_valid_image_name("alpine:latest --extra-arg")
    assert "No whitespace accepted in image names" in str(exc)

    with pytest.raises(ValueError) as exc:
        assert_is_valid_image_name("alpine:latest?param")
    assert "No parameters, query parameters, or fragments are supported" in str(exc)

    with pytest.raises(ValueError) as exc:
        assert_is_valid_image_name("http://alpine:latest")
    assert "Unsupported scheme 'http'" in str(exc)


def test_is_valid_imagestore_name():
    assert assert_is_valid_imagestore_name("public")

    with pytest.raises(ValueError) as exc:
        assert_is_valid_imagestore_name("invalid/name")
    assert "Unsupported imagestore name `invalid/name`: Only `public` is accepted" in str(exc)


def test_assert_is_valid_resource_name():
    assert assert_is_valid_resource_name("valid_name42")

    with pytest.raises(ValueError) as exc:
        assert_is_valid_resource_name("invalid name")

    with pytest.raises(ValueError) as exc:
        assert_is_valid_resource_name("invalid/name")
    assert "A resource name should only be constituted of alphanumeric characters, or underscores" in str(exc)


def test_ImageStoreStorage():
    imgstore = ImageStoreStorage(images=None)
    assert imgstore.images == {}

    raw = {
        "images": {
            "mars": {"name": "docker://registry.freedesktop.org/gfx-ci/ci-tron/machine-registration:latest"},
            "mars2": {"name": "registry.freedesktop.org/gfx-ci/ci-tron/machine-registration:latest"},
            "shortname": {"name": "shortname", "tls_verify": "false", "platform": 'linux/arm64'},
        }
    }

    imgstore = ImageStoreStorage(**raw)
    assert imgstore.images == {
        "mars": ContainerImageStorage(name=raw['images']["mars"]['name'], tls_verify=True, platform='linux/amd64'),
        "mars2": ContainerImageStorage(name=raw['images']["mars2"]['name'], tls_verify=True, platform='linux/amd64'),
        "shortname": ContainerImageStorage(name=raw['images']["shortname"]['name'], tls_verify=False,
                                           platform='linux/arm64'),
    }


def test_convert_human_size_to_bytes():
    for exponent in ["", "B", "iB"]:
        assert convert_human_size_to_bytes(f"42{exponent}") == 42

    assert convert_human_size_to_bytes("42k") == 42 * 1024
    assert convert_human_size_to_bytes("42kiB") == 42 * 1024
    assert convert_human_size_to_bytes("42kB") == 42 * 1000

    assert convert_human_size_to_bytes("42M") == 42 * 1024**2
    assert convert_human_size_to_bytes("42G") == 42 * 1024**3
    assert convert_human_size_to_bytes("42T") == 42 * 1024**4
    assert convert_human_size_to_bytes("42P") == 42 * 1024**5

    with pytest.raises(ValueError):
        convert_human_size_to_bytes("-42")

    with pytest.raises(ValueError):
        convert_human_size_to_bytes("42 k")

    with pytest.raises(ValueError):
        convert_human_size_to_bytes("42 kib")


def test_NbdStorage():
    with pytest.raises(ValueError) as exc:
        NbdStorage()
    assert "No backing were selected" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        NbdStorage(url="https://hello/world", size="10G")
    assert "Only one backing may be selected at a time" in str(exc.value)


@patch("server.job.nbd.create_tmp_raw_backing", return_value="/tmp/raw/backing")
@patch("server.job.nbd.Nbd")
def test_NbdStorage__setup_with_size_backing(nbd_mock, create_tmp_raw_backing_mock):
    job_nbd = NbdStorage(readonly=False, max_connections=5, size="1kB")

    want = Nbd(name="MyName", backing=create_tmp_raw_backing_mock.return_value, backing_read_only=False,
               export_as_read_only=job_nbd.readonly, max_connections=job_nbd.max_connections)

    nbd = job_nbd.setup(name=want.name, timeout=42)
    create_tmp_raw_backing_mock.assert_called_once_with(1000)
    assert nbd == nbd_mock.return_value
    nbd.setup.assert_called_once_with(timeout=42)


@patch("server.job.nbd.Nbd")
def test_NbdStorage__setup_with_url_backing(nbd_mock):
    job_nbd = NbdStorage(url="https://hello/world")

    artifact_cache = MagicMock()
    artifact_file_path_mock = artifact_cache.get_or_reuse_instance.return_value.get_filepath
    artifact_file_path_mock.return_value = "/tmp/url/backing"
    want = Nbd(name="MyName", backing=artifact_file_path_mock.return_value, backing_read_only=True,
               export_as_read_only=job_nbd.readonly, max_connections=job_nbd.max_connections)

    nbd = job_nbd.setup(name=want.name, artifact_cache=artifact_cache, polling_delay=1)
    artifact_cache.get_or_reuse_instance.assert_called_once_with(url=job_nbd.url, name=want.name)
    artifact_cache.get_or_reuse_instance.return_value.get_filepath.assert_called_once_with(polling_delay=1)
    assert nbd == nbd_mock.return_value
    nbd.setup.assert_called_once_with(timeout=None)


def test_StorageDeployment():
    raw1 = {
        "imagestore": {
            "public": {
                "images": {
                    "mars": {"name": "mars1"},
                }
            }
        }
    }

    raw2 = {
        "imagestore": {
            "public": {
                "images": {
                    "mars2": {"name": "mars2"},
                }
            }
        }
    }

    storage = StorageDeployment(**raw1).update(StorageDeployment(**raw2))
    assert storage.imagestore["public"].images == {
        "mars": ContainerImageStorage(name="mars1", tls_verify=True, platform='linux/amd64'),
        "mars2": ContainerImageStorage(name="mars2", tls_verify=True, platform='linux/amd64'),
    }


def test_Deployment__duplicated_imagestore_name():
    raw = {
        "start": {"storage": {"imagestore": {"public": {"images": {
            "mars1": {"name": "mars1"},
            "mars2": {"name": "mars2"},
        }}}}},
        "continue": {"storage": {"imagestore": {"public": {"images": {
            "mars1": {"name": "mars1"},
            "mars2": {"name": "mars2"},
        }}}}},
    }

    with pytest.raises(ValueError) as exc:
        Deployment(**raw)
    assert "Can't redefine container images the continue deployment: public/mars1, public/mars2" in str(exc)


def test_DeploymentState():
    deployment = DeploymentState()

    assert deployment.kernel is None
    assert deployment.initramfs is None

    assert deployment.update({}) == deployment

    assert deployment.kernel is None
    assert deployment.initramfs is None

    deployment.update({"kernel": {"url": "https://host.tld/kernel_url", "cmdline": "cmdline"},
                       "initramfs": {"url": "https://host.tld/initramfs_url"},
                       "dtb": {"url": "https://host.tld/dtb_url"}})

    assert deployment.kernel.url == "https://host.tld/kernel_url"
    assert deployment.initramfs[0].url == "https://host.tld/initramfs_url"
    assert deployment.kernel.cmdline == "cmdline"

    assert str(deployment) == ("DeploymentState(kernel=KernelDeployment(url=https://host.tld/kernel_url, "
                               "cmdline=cmdline), initramfs=ArtifactDeployment(url=https://host.tld/initramfs_url), "
                               "dtb=ArtifactDeployment(url=https://host.tld/dtb_url))")

    # Update only one kernel field
    deployment.update({"kernel": {"cmdline": "cmdline2"}})
    assert deployment.kernel.url == "https://host.tld/kernel_url"
    assert deployment.initramfs[0].url == "https://host.tld/initramfs_url"
    assert deployment.kernel.cmdline == "cmdline2"


def test_DhcpRequestMatcher():
    all_fields = {
        "architecture": "x86_64",
        "firmware": "uboot",
        "protocol": "http",
        "vendor_class": "vendor class",
        "user_class": "user class",
        "uuid": "uuid"
    }

    # Empty means matches everything!
    assert DhcpRequestMatcher().matches(MagicMock())
    assert DhcpRequestMatcher().matches(MagicMock(**all_fields))

    # Try adding variables and make sure it still matches
    match_fields = {}
    for var, value in all_fields.items():
        match_fields[var] = value
        assert DhcpRequestMatcher(**match_fields).matches(MagicMock(**all_fields))

    # Ensure that if an argument in DhcpClientRequestMatcher is missing from the request, it does not count as a match
    assert not DhcpRequestMatcher(architecture="x86_64").matches(MagicMock())

    # Ensure that variables with different values do not count as a match
    assert not DhcpRequestMatcher(architecture="x86_64").matches(MagicMock(architecture="arm64"))

    # Ensure that having multiple acceptable values work as expected, but not an unexpected one
    matcher = DhcpRequestMatcher(architecture=["x86_64", "arm64"])
    assert matcher.matches(MagicMock(architecture="arm64"))
    assert matcher.matches(MagicMock(architecture="x86_64"))
    assert not matcher.matches(MagicMock(architecture="riscv64"))

    # Ensure that strings can be matched using regular expressions
    matcher = DhcpRequestMatcher(uuid="uuid.*")
    assert matcher.matches(MagicMock(uuid="uuid"))
    assert matcher.matches(MagicMock(uuid="uuid after"))
    assert not matcher.matches(MagicMock(uuid="before uuid"))

    # Ensure that invalid regular expressions don't explode
    matcher = DhcpRequestMatcher(uuid="*uuid*")
    assert matcher.matches(MagicMock(uuid="*uuid*"))
    assert not matcher.matches(MagicMock(uuid="uuid"))

    # Ensure that MAC addresses can use regular expressions
    matcher = DhcpRequestMatcher(mac_address=["b8:27:eb:.*", "2c:cf:67:.*",
                                              "d8:3a:dd:.*", "dc:a6:32:.*",
                                              "e4:5f:01:.*"])
    assert matcher.matches(MagicMock(mac_address=MacAddress("d8:3a:dd:a3:8b:78")))
    assert not matcher.matches(MagicMock(mac_address=MacAddress("d9:3a:dd:a3:8b:78")))


def test_DhcpDeployment__match():
    deployment = DhcpDeployment(options={"hostname": "helloworld"})
    request = MagicMock()

    # Make sure that matching without a matcher set always return True
    assert deployment.matches(None)

    # Make sure that calling .matches() on a deployment gets forwarded to the matcher
    deployment.match = MagicMock()
    assert deployment.matches(request) == deployment.match.matches.return_value
    deployment.match.matches.assert_called_once_with(request)


def store_kwargs_in_mock(*args, **kwargs):
    return MagicMock(args=args, kwargs=kwargs)


@patch("server.artifact.uimage.UImageArtifact.__new__", side_effect=store_kwargs_in_mock)
def test_UBootArtifactFormatDeployment__format(uimage_mock):
    job_artifact = UBootArtifactFormatDeployment(**{"architecture": "arm64", "compression": "none",
                                                    "os": "linux", "type": "script"})

    artifact = MagicMock()
    ret = job_artifact.format(job_artifact=None, artifact=artifact, path=None)

    assert ret.kwargs == {
        "artifact": artifact,
        "architecture": CPUArch.ARM64,
        "compression": UImageFormatCompression.NONE,
        "os": UImageFormatOS.LINUX,
        "type": UImageFormatType.SCRIPT
    }


def test_ArtifactArchiveFormatDeployment__match():
    artifact = ArtifactArchiveFormatDeployment(match="helloworld")

    assert artifact.extension == ArchiveFormat.NONE
    assert artifact.compression == ArchiveCompression.NONE
    assert artifact.keep == [ArtifactArchiveFormatKeep(path="helloworld")]

    # Test that keep and match are mutually exclusive
    with pytest.raises(ValueError) as exc:
        ArtifactArchiveFormatDeployment(match="helloworld",
                                        keep=[ArtifactArchiveFormatKeep(path="helloworld")])
    assert "The `match` is incompatible with `keep`" in str(exc)

    # Test that keep and match are mutually exclusive
    with pytest.raises(ValueError) as exc:
        artifact = ArtifactDeployment(data=b"Hello world")
        ArtifactArchiveFormatDeployment(match="helloworld",
                                        add=[ArtifactArchiveAddArtifact(path="helloworld", artifact=artifact)])
    assert "The `match` is incompatible with `add`" in str(exc)


@patch("server.artifact.archive.ArchiveArtifact.__new__", side_effect=store_kwargs_in_mock)
def test_ArtifactArchiveFormatDeployment__format__match(archiveartifact_mock):
    artifact_fmt = ArtifactFormatDeployment(archive=ArtifactArchiveFormatDeployment(match=r"firmware-.*/boot/\1"))
    job_artifact = StorageArtifactDeployment(path="/(.*)", format=[artifact_fmt])
    artifact_io = MagicMock()

    ret = artifact_fmt.format(job_artifact, artifact_io, "/bootcode.sig")
    assert ret.kwargs == {
        "artifact": artifact_io,
        "format": ArchiveFormat.NONE,
        "keep": [ArtifactKeep(path=re.compile("firmware-.*/boot/bootcode.sig"))],
        "compression": ArchiveCompression.NONE,
        "add": [],
    }


def test_ArtifactArchiveFormatKeep__to_artifact_keep():
    keep = ArtifactArchiveFormatKeep(path=r"firmware-.*/boot/(.*)", rewrite=r"/usr/lib/\1")

    # No job artifact path (can be an initrd, kernel, ...) means keep self.path verbatim
    result = keep.to_artifact_keep(job_artifact_path=None, request_path="/initrd")
    assert result == ArtifactKeep(path=re.compile(keep.path), rewrite=keep.rewrite)

    # Job artifact path available, but rewriting failed which means keep self.path verbatim
    result = keep.to_artifact_keep(job_artifact_path="/helloworld", request_path="/bootcode.bin")
    assert result == ArtifactKeep(path=re.compile(keep.path), rewrite=keep.rewrite)

    # Invalid job_artifact_path regex means keep self.path verbatim
    result = keep.to_artifact_keep(job_artifact_path="*", request_path="/bootcode.bin")
    assert result == ArtifactKeep(path=re.compile(keep.path), rewrite=keep.rewrite)


@patch("server.artifact.archive.ArchiveArtifact.__new__", side_effect=store_kwargs_in_mock)
def test_ArtifactArchiveFormatDeployment__format__keep_and_add_with_rewrite(archiveartifact_mock):
    keep = ArtifactArchiveFormatKeep(path=r"firmware-.*/boot/\1")
    add = ArtifactArchiveAddArtifact(path=r"mnt/\1", artifact=ArtifactDeployment(data=b"bootcode"))
    artifact_fmt = ArtifactFormatDeployment(archive=ArtifactArchiveFormatDeployment(extension="cpio",
                                                                                    keep=[keep], add=[add]))
    job_artifact = StorageArtifactDeployment(path="/(.*)", format=[artifact_fmt])

    artifact_io = MagicMock()
    ret = artifact_fmt.format(job_artifact, artifact_io, "/bootcode.bin")

    artifact_adds = ret.kwargs.pop('add')
    assert len(artifact_adds) == 1
    artifact_add = artifact_adds[0]
    assert isinstance(artifact_add.artifact, DataArtifact)
    assert artifact_add.artifact.read() == b"bootcode"
    assert artifact_add.path == "mnt/bootcode.bin"
    assert artifact_add.mode == 0o100644

    assert ret.kwargs == {
        "artifact": artifact_io,
        "format": ArchiveFormat.CPIO,
        "keep": [ArtifactKeep(path=re.compile("firmware-.*/boot/bootcode.bin"))],
        "compression": ArchiveCompression.NONE,
    }


@patch("server.artifact.archive.ArchiveArtifact.__new__", side_effect=store_kwargs_in_mock)
def test_ArtifactArchiveAddArtifact__to_artifact_add(archiveartifact_mock):
    artifact = ArtifactDeployment(data=b"Hello world")

    # No job artifact path (can be an initrd, kernel, ...) means keep self.path verbatim
    add = ArtifactArchiveAddArtifact(path=r"/etc/hosts", artifact=artifact)
    add.artifact = MagicMock()
    result = add.to_artifact_add(job_artifact_path=None, request_path="/hosts.cpio")
    add.artifact.open.assert_called_once_with(path="/hosts.cpio-/etc/hosts", polling_delay=0.05, artifact_cache=None)
    assert result == ArtifactAdd(artifact=add.artifact.open.return_value, path="/etc/hosts", mode=0o100644)

    # Job artifact path available, but rewriting failed which means keep self.path verbatim
    add = ArtifactArchiveAddArtifact(path=r"/myfile", artifact=artifact)
    add.artifact = MagicMock()
    result = add.to_artifact_add(job_artifact_path="/helloworld", request_path="/modules.zip")
    add.artifact.open.assert_called_once_with(path="/modules.zip-/myfile", polling_delay=0.05,
                                              artifact_cache=None)
    assert result == ArtifactAdd(artifact=add.artifact.open.return_value, path=r"/myfile", mode=0o100644)

    # Invalid job_artifact_path regex means keep self.path verbatim
    add = ArtifactArchiveAddArtifact(path=r"/bootcode.bin", artifact=artifact)
    add.artifact = MagicMock()
    result = add.to_artifact_add(job_artifact_path="*", request_path="/modules.zip")
    add.artifact.open.assert_called_once_with(path="/modules.zip-/bootcode.bin", polling_delay=0.05,
                                              artifact_cache=None)
    assert result == ArtifactAdd(artifact=add.artifact.open.return_value, path=r"/bootcode.bin", mode=0o100644)


# Job


def test_Job__simple():
    simple_job = """
version: 1
target:
  id: "b4:2e:99:f0:76:c5"
console_patterns:
  session_end:
    regex: "session_end"
deployment:
  start:
    kernel:
      url: "https://host.tld/kernel_url"
      cmdline:
        - my
        - start cmdline
    initramfs:
      url: "https://host.tld/initramfs_url"
"""
    job = Job.render_with_resources(simple_job)

    assert job.version == 1
    assert job.deadline == datetime.max

    assert job.target.id == "b4:2e:99:f0:76:c5"
    assert job.target.tags == []

    assert job.deployment_start.kernel.url == "https://host.tld/kernel_url"
    assert job.deployment_start.initramfs[0].url == "https://host.tld/initramfs_url"
    assert job.deployment_start.kernel.cmdline == "my start cmdline"
    assert job.deployment_start.fastboot is None
    assert job.deployment_start.artifacts == {
        "https://host.tld/kernel_url": {("kernel", ): job.deployment_start.kernel},
        "https://host.tld/initramfs_url": {("initramfs", "0"): job.deployment_start.initramfs[0]},
    }
    assert job.deployment_start.container_images == {}
    assert job.deployment_start.nbd_storages == {}

    assert job.deployment_continue.kernel.url == job.deployment_start.kernel.url
    assert job.deployment_continue.initramfs[0].url == job.deployment_start.initramfs[0].url
    assert job.deployment_continue.kernel.cmdline == job.deployment_start.kernel.cmdline
    assert job.deployment_continue.fastboot == job.deployment_start.fastboot
    assert job.deployment_continue.artifacts == job.deployment_start.artifacts
    assert job.deployment_continue.container_images == job.deployment_start.container_images
    assert job.deployment_continue.nbd_storages == job.deployment_start.container_images

    assert job.deployment.artifacts == {
        "https://host.tld/kernel_url": {
            ("start", "kernel", ): job.deployment_start.kernel,
            ("continue", "kernel", ): job.deployment_continue.kernel
        },
        "https://host.tld/initramfs_url": {
            ("start", "initramfs", "0"): job.deployment_start.initramfs[0],
            ("continue", "initramfs", "0"): job.deployment_continue.initramfs[0]
        },
    }

    # Make sure the job's __str__ method does not crash
    str(job)


def test_Job__override_continue():
    override_job = """
version: 1
deadline: "2021-03-31 00:00:00"
target:
  id: "b4:2e:99:f0:76:c6"
  tags: ["amdgpu:gfxversion::gfx10"]
console_patterns:
  session_end:
    regex: "session_end"
deployment:
  start:
    storage:
      imagestore:
        public:
          images:
             base_gateway:
               name: registry.freedesktop.org/gfx-ci/ci-tron/gateway-base:latest
               tls_verify: false
               platform: invalid/platform
               pull: missing
      nbd:
        root:
          size: 10G
    kernel:
      url: "https://host.tld/kernel_url"
      cmdline:
        defaults:
          - my
          - default cmdline
    initramfs:
      url: "https://host.tld/initramfs_url"
  continue:
    storage:
      http:
        - path: "/helloworld"
          url: "https://host.tld/helloworld"
      imagestore:
        public:
          images:
            gateway:
              name: registry.freedesktop.org/gfx-ci/ci-tron/gateway:latest
      nbd:
        swap:
          size: 8G
    kernel:
      url: "https://host.tld/kernel_url_2"
      cmdline: "my continue cmdline"
    initramfs:
      url: "https://host.tld/initramfs_url_2"
    dtb:
      url: "https://host.tld/dtb_url_2"
    fastboot:
      header_version: 42
      base: 0x123456789
      kernel_offset: 0xcafe
      ramdisk_offset: 0xc0de
      dtb_offset: 0xbeef
      tags_offset: 0xdead
      board: "myboard"
      pagesize: 16384
"""
    job = Job.render_with_resources(override_job)

    assert job.version == 1
    assert job.deadline == datetime.fromisoformat("2021-03-31 00:00:00")

    assert job.target.id == "b4:2e:99:f0:76:c6"
    assert job.target.tags == ["amdgpu:gfxversion::gfx10"]

    assert job.deployment_start.kernel.url == "https://host.tld/kernel_url"
    assert job.deployment_start.initramfs[0].url == "https://host.tld/initramfs_url"
    assert job.deployment_start.kernel.cmdline == "my default cmdline"
    assert job.deployment_start.dtb is None
    assert job.deployment_start.artifacts == {
        "https://host.tld/kernel_url": {("kernel", ): job.deployment_start.kernel},
        "https://host.tld/initramfs_url": {("initramfs", "0"): job.deployment_start.initramfs[0]},
    }
    assert job.deployment_start.container_images == {
        "public": {
            "base_gateway": ImageStoreImage(store_name="public", platform="invalid/platform", tls_verify=False,
                                            image_name="registry.freedesktop.org/gfx-ci/ci-tron/gateway-base:latest",
                                            pull_policy=ImageStorePullPolicy.MISSING)
        }
    }

    assert job.deployment_start.nbd_storages == {
        "root": NbdStorage(size="10G")
    }

    assert job.deployment_continue.kernel.url == "https://host.tld/kernel_url_2"
    assert job.deployment_continue.initramfs[0].url == "https://host.tld/initramfs_url_2"
    assert job.deployment_continue.kernel.cmdline == "my default cmdline my continue cmdline"
    assert job.deployment_continue.dtb[0].url == "https://host.tld/dtb_url_2"
    assert job.deployment_continue.artifacts == {
        "https://host.tld/kernel_url_2": {("kernel", ): job.deployment_continue.kernel},
        "https://host.tld/initramfs_url_2": {("initramfs", "0"): job.deployment_continue.initramfs[0]},
        "https://host.tld/dtb_url_2": {("dtb", "0"): job.deployment_continue.dtb[0]},
        "https://host.tld/helloworld": {("storage", "http", "0"): job.deployment_continue.storage.http[0]},
    }
    assert job.deployment_continue.container_images == {
        "public": {
            "base_gateway": ImageStoreImage(store_name="public", platform="invalid/platform", tls_verify=False,
                                            image_name="registry.freedesktop.org/gfx-ci/ci-tron/gateway-base:latest",
                                            pull_policy=ImageStorePullPolicy.MISSING),
            "gateway": ImageStoreImage(store_name="public", platform="linux/amd64", tls_verify=True,
                                       image_name="registry.freedesktop.org/gfx-ci/ci-tron/gateway:latest",
                                       pull_policy=ImageStorePullPolicy.RELAXED_ALWAYS)
        }
    }

    assert job.deployment_continue.nbd_storages == {
        "root": NbdStorage(size="10G"),
        "swap": NbdStorage(size="8G"),
    }

    assert str(job.deployment_continue.fastboot) == ("<Fastboot: header_version=42, base=0x123456789, "
                                                     "kernel_offset=0xcafe, ramdisk_offset=0xc0de, dtb_offset=0xbeef, "
                                                     "tags_offset=0xdead, board=myboard, pagesize=16384>")

    assert job.deployment.artifacts == {
        "https://host.tld/helloworld": {("continue", "storage", "http", "0"): job.deployment_continue.storage.http[0]},
        "https://host.tld/kernel_url": {("start", "kernel", ): job.deployment_start.kernel},
        "https://host.tld/initramfs_url": {("start", "initramfs", "0"): job.deployment_start.initramfs[0]},
        "https://host.tld/kernel_url_2": {("continue", "kernel", ): job.deployment_continue.kernel},
        "https://host.tld/initramfs_url_2": {("continue", "initramfs", "0"): job.deployment_continue.initramfs[0]},
        "https://host.tld/dtb_url_2": {("continue", "dtb", "0"): job.deployment_continue.dtb[0]},
    }
    assert job.deployment.container_images == job.deployment_continue.container_images
    assert job.deployment.nbd_storages == job.deployment_continue.nbd_storages


class MockMachine:
    @property
    def ready_for_service(self):
        return True

    @property
    def id(self):
        return "b4:2e:99:f0:76:c5"

    @property
    def tags(self):
        return ["some", "tags"]

    @property
    def local_tty_device(self):
        return "ttyS0"

    @property
    def ip_address(self):
        return "10.42.0.123"

    @property
    def firmware_boot_time(self):
        return 31.2

    @property
    def safe_attributes(self):
        return {
            "base_name": "base_name",
            "full_name": "full_name",
            "tags": self.tags,
            "ip_address": self.ip_address,
            "local_tty_device": self.local_tty_device,
            "ready_for_service": self.ready_for_service,
            "firmware_boot_time": self.firmware_boot_time,
        }


class MockBucket:
    @property
    def name(self):
        return "bucket_name"

    @property
    def minio(self):
        return MagicMock(url="minio_url")

    @property
    def credentials(self):
        return MagicMock(dut=("access", "secret"))


@patch('server.config.job_environment_vars')
def test_Job__sample(job_env):
    job_env.return_value = {'MINIO_URL': 'http://localhost:9000/testing-url',
                            'NTP_PEER': '10.42.0.1',
                            'PULL_THRU_REGISTRY': '10.42.0.1:8001'}

    m = MockMachine()
    job = Job.from_path("src/valve_gfx_ci/executor/server/tests/sample_job.yml", m)

    assert job.version == 1
    assert job.deadline == datetime.fromisoformat("2021-03-31 00:00:00")

    assert job.target.id == m.id
    assert job.target.tags == m.tags

    assert job.deployment_start.kernel.url == "http://localhost:9000/testing-url/test-kernel"
    assert job.deployment_start.initramfs[0].url == "http://localhost:9000/testing-url/test-initramfs"

    assert job.deployment_start.kernel.cmdline == 'b2c.container="docker://10.42.0.1:8001/infra/machine-registration:latest check" b2c.ntp_peer="10.42.0.1" b2c.pipefail b2c.cache_device=auto b2c.container="-v /container/tmp:/storage docker://10.42.0.1:8002/tests/mesa:12345" console=ttyS0,115200 earlyprintk=vga,keep SALAD.machine_id=b4:2e:99:f0:76:c5 extra=""'  # noqa: E501

    assert job.deployment_continue.kernel.url == "http://localhost:9000/testing-url/test-kernel"
    assert job.deployment_continue.initramfs[0].url == "http://localhost:9000/testing-url/test-initramfs"
    assert job.deployment_continue.kernel.cmdline == 'b2c.container="docker://10.42.0.1:8001/infra/machine-registration:latest check" b2c.ntp_peer=10.42.0.1 b2c.pipefail b2c.cache_device=auto b2c.container="-v /container/tmp:/storage docker://10.42.0.1:8002/tests/mesa:12345 resume"'  # noqa: E501


def test_Job__invalid_format():
    job = """
version: 1
target:
  id: "b4:2e:99:f0:76:c6"
console_patterns:
  session_end:
    regex: "session_end"
  reboot:
    regex: "toto"
deployment:
  start:
    kernel:
      url: "https://host.tld/kernel_url"
      cmdline:
        - my
        - start cmdline
    initramfs:
      url: "https://host.tld/initramfs_url"
"""

    with pytest.raises(ValueError) as exc:
        Job.render_with_resources(job)

    assert "console_patterns.reboot\n  Unexpected keyword argument" in str(exc.value)


@patch('server.config.job_environment_vars')
def test_Job__from_machine(job_env):
    job_env.return_value = {'NTP_PEER': '10.42.0.1'}

    simple_job = """
#!jinja2
version: 1
target:
  id: {{ machine_id }}
console_patterns:
  session_end:
    regex: "session_end"
deployment:
  start:
    kernel:
      url: "https://host.tld/kernel_url"
      cmdline:
        - my {{ minio_url }}
        - start cmdline {{ ntp_peer }}
        - hostname {{ machine.full_name }}
        - extra {{ extra }}
    initramfs:
      url: "https://host.tld/initramfs_url"
"""
    job = Job.render_with_resources(simple_job, MockMachine(), MockBucket(), extra="parameter")

    assert job.version == 1
    assert job.deadline == datetime.max

    assert job.target.id == "b4:2e:99:f0:76:c5"
    assert job.target.tags == []

    assert job.deployment_start.kernel.url == "https://host.tld/kernel_url"
    assert job.deployment_start.initramfs[0].url == "https://host.tld/initramfs_url"
    assert (job.deployment_start.kernel.cmdline == "my minio_url start cmdline 10.42.0.1 hostname full_name "
                                                   "extra parameter")

    assert job.deployment_continue.kernel.url == job.deployment_start.kernel.url
    assert job.deployment_continue.initramfs[0].url == job.deployment_start.initramfs[0].url
    assert job.deployment_continue.kernel.cmdline == job.deployment_start.kernel.cmdline


def test_Job__watchdogs():
    override_job = """
version: 1
target:
  id: "b4:2e:99:f0:76:c6"
timeouts:
  watchdogs:
    wd1:
      minutes: 1
console_patterns:
  session_end:
    regex: "session_end"
  watchdogs:
    wd1:
      start:
        regex: "start"
      reset:
        regex: "reset"
      stop:
        regex: "stop"
deployment:
  start:
    kernel:
      url: "https://host.tld/kernel_url"
      cmdline: "cmdline"
    initramfs:
      url: "https://host.tld/initramfs_url"
"""
    job = Job.render_with_resources(override_job)
    assert job.console_patterns.watchdogs["wd1"].timeout == job.timeouts.watchdogs["wd1"]

    # Test that getting the string does not explode
    str(job)


# Job vars

@mock.patch.dict(os.environ, {"EXECUTOR_JOB__FDO_PROXY_REGISTRY": "10.10.10.1:1234"})
def test_server_config_job_environment_vars():
    ret = server.config.job_environment_vars()

    assert "MINIO_URL" in ret

    assert "FDO_PROXY_REGISTRY" in ret
    assert ret["FDO_PROXY_REGISTRY"] == "10.10.10.1:1234"
