from unittest.mock import patch, MagicMock

import pytest

from server.job_source import JobSource, JobSourceExternalCommand


def create_job_source(expose_runners: bool = True, dut_exposed: bool = False) -> JobSource:
    job_src = JobSource(job_src=MagicMock(expose_runners=expose_runners),
                        db_dut=MagicMock(),
                        db_dut_job_src=MagicMock(exposed=dut_exposed))
    job_src._run_job = MagicMock()
    return job_src


def test_JobSourceExternalCommand__setup_job():
    job_src = JobSourceExternalCommand(None, None, None)
    # Default implementation should return True
    assert job_src._setup_job() is True


def test_JobSource__try_cancel_job_pickup():
    job_src = JobSource(None, None, None)
    # Default implementation should return False
    assert job_src._try_cancel_job_pickup() is False


def test_JobSource_run_job():
    def _run_job__success():
        nonlocal callback_called

        callback_called = True

        # Check the job_cookie
        assert job_src.job_cookie.startswith(f"{JobSource.JOB_SOURCE_NAME}_")

        return True

    def _run_job__raise():
        raise ValueError("Run Error")

    # Make sure we don't run if we are not supposed to expose the DUT
    assert not create_job_source(expose_runners=False, dut_exposed=False).run_job()
    assert not create_job_source(expose_runners=True, dut_exposed=False).run_job()

    # Run then check that our callback got called and the job_cookie got reset
    job_src = create_job_source(expose_runners=True, dut_exposed=True)
    job_src._run_job = _run_job__success
    callback_called = False
    assert job_src.run_job()
    assert callback_called
    assert job_src.job_cookie is None

    # Check the exception codepath
    job_src = create_job_source(expose_runners=True, dut_exposed=True)
    job_src._run_job = _run_job__raise
    assert not job_src.run_job()

    # Check the "not exposed" codepath
    job_src = create_job_source(expose_runners=True, dut_exposed=True)
    job_src._run_job = _run_job__raise
    assert not job_src.run_job()


def test_JobSource_assert_job_from_us():
    job_src = create_job_source()
    job_src.job_cookie = job_cookie = MagicMock()

    with pytest.raises(ValueError) as exc:
        job_src.assert_job_from_us(None)
    assert "The job cookie doesn't match" in str(exc)

    job_src.assert_job_from_us(job_cookie)


def test_JobSourceExternalCommand__run_job():
    job_src = JobSourceExternalCommand(None, None, None)
    job_src._subprocess_kwargs = MagicMock(return_value={"arg1": 1, "arg2": 2})

    # Ensure that if _setup_job fails, we do not start the external command and return False
    with patch("subprocess.Popen") as popen_mock:
        job_src._setup_job = MagicMock(return_value=False)
        assert not job_src._run_job()
        job_src._setup_job.assert_called_once()
        popen_mock.assert_not_called()

    job_src._setup_job = MagicMock(return_value=True)

    with patch("server.job_source.TemporaryFile") as output_mock:
        output = output_mock.return_value.__enter__.return_value

        # Mock Phase 1 timeout with successful cancellation
        with patch("subprocess.Popen") as popen_mock:
            popen_mock.return_value.poll = MagicMock(side_effect=[None, None])
            job_src.job_submitted_event = MagicMock(is_set=MagicMock(side_effect=[False, False, False]))
            job_src._try_cancel_job_pickup = MagicMock(return_value=True)
            job_src.stop_event = MagicMock(is_set=MagicMock(return_value=False))
            with patch("time.monotonic", side_effect=[0, job_src.JOB_PICKUP_TIMEOUT_SECONDS + 1]):
                assert not job_src._run_job()
                assert job_src._try_cancel_job_pickup.call_count == 2

        output_mock.reset_mock()

        # Mock Phase 2 timeout - job picked up but never submitted
        with patch("subprocess.Popen") as popen_mock:
            popen_mock.return_value.poll = MagicMock(side_effect=[None, None, None, None])
            popen_mock.return_value.returncode = None
            job_src.job_submitted_event = MagicMock(is_set=MagicMock(side_effect=[False, False, False,
                                                                                  False, False, False]))
            job_src._try_cancel_job_pickup = MagicMock(return_value=False)  # Cancellation fails
            job_src.stop_event = MagicMock(is_set=MagicMock(return_value=False))
            # time_start, Phase1 check, submission_start, Phase2 check1, Phase2 check2 (timeout)
            with patch("time.monotonic", side_effect=[0, job_src.JOB_PICKUP_TIMEOUT_SECONDS + 1,
                                                      job_src.JOB_PICKUP_TIMEOUT_SECONDS + 1,
                                                      job_src.JOB_PICKUP_TIMEOUT_SECONDS + 2,
                                                      job_src.JOB_PICKUP_TIMEOUT_SECONDS +
                                                      job_src.JOB_SUBMISSION_TIMEOUT_SECONDS + 2]):
                assert not job_src._run_job()
                assert job_src._try_cancel_job_pickup.call_count == 2

        output_mock.reset_mock()

        # Mock a successful run with job submission and cut short by a stop signal
        with patch("subprocess.Popen") as popen_mock:
            popen_mock.return_value.poll = MagicMock(side_effect=[None, None, None, None, None, None])
            popen_mock.return_value.returncode = None
            job_src.job_submitted_event = MagicMock(is_set=MagicMock(side_effect=[False, True, True, True,
                                                                                  True, True, True]))
            job_src.stop_event = MagicMock(is_set=MagicMock(side_effect=[False, False, True]))
            assert job_src._run_job()
            output_mock.assert_called_once_with(mode='w+t')
            popen_mock.assert_called_once_with(arg1=1, arg2=2, stdout=output, stderr=output, text=True)
            job_src.job_submitted_event.wait.assert_called_once_with(job_src.POLLING_SECONDS)
            output.seek.assert_not_called()
            output.read.assert_not_called()
            job_src.stop_event.is_set.assert_called_with()
            job_src.stop_event.wait.assert_called_with(job_src.POLLING_SECONDS)

        # Mock a job source exiting before job submission
        with patch("subprocess.Popen") as popen_mock:
            popen_mock.return_value.poll = MagicMock(return_value=1)
            popen_mock.return_value.returncode = 1
            job_src.job_submitted_event = MagicMock(is_set=MagicMock(side_effect=[False, False, False]))
            job_src.stop_event = MagicMock()
            with patch("time.monotonic", side_effect=[0, 1, job_src.JOB_SUBMISSION_TIMEOUT_SECONDS]):
                assert not job_src._run_job()
                job_src.job_submitted_event.wait.assert_not_called()
                popen_mock.return_value.kill.assert_not_called()
                popen_mock.return_value.wait.assert_not_called()
                output.seek.assert_called_once_with(0)
                output.read.assert_called_once_with()
                job_src.stop_event.is_set.assert_not_called()
                job_src.stop_event.wait.assert_not_called()


def test_JobSourceExternalCommand__cleanup_on_termination():
    """Test that processes are properly terminated and cleaned up"""
    job_src = JobSourceExternalCommand(None, None, None)
    job_src._setup_job = MagicMock(return_value=True)
    job_src._subprocess_kwargs = MagicMock(return_value={})

    # Test graceful termination (process still running when cleanup happens)
    with patch("subprocess.Popen") as popen_mock:
        proc_mock = popen_mock.return_value
        proc_mock.poll = MagicMock(side_effect=[None, None, None, None, None])
        proc_mock.wait = MagicMock()
        proc_mock.returncode = None

        job_src.job_submitted_event = MagicMock(
            is_set=MagicMock(side_effect=[False, False, False, False, False, False])
        )
        job_src.stop_event = MagicMock(
            is_set=MagicMock(side_effect=[False, True])
        )

        with patch("time.monotonic", side_effect=[0, 1, 1, 1, 60]):
            result = job_src._run_job()

        assert result is False
        proc_mock.terminate.assert_called_once()
        proc_mock.wait.assert_called_once_with(5)
        proc_mock.kill.assert_not_called()

    # Test forceful kill (process doesn't respond to terminate)
    with patch("subprocess.Popen") as popen_mock:
        from subprocess import TimeoutExpired
        proc_mock = popen_mock.return_value
        proc_mock.poll = MagicMock(side_effect=[None, None, None, None, None])
        proc_mock.wait = MagicMock(side_effect=TimeoutExpired('cmd', 5))
        proc_mock.kill = MagicMock()
        proc_mock.returncode = None

        job_src.job_submitted_event = MagicMock(
            is_set=MagicMock(side_effect=[False, False, False, False, False, False, False])
        )
        job_src.stop_event = MagicMock(
            is_set=MagicMock(side_effect=[False, True])
        )

        with patch("time.monotonic", side_effect=[0, 1, 1, 1, 60]):
            result = job_src._run_job()

        assert result is False
        proc_mock.terminate.assert_called_once()
        proc_mock.wait.assert_called_once_with(5)
        proc_mock.kill.assert_called_once()

    # Test process already exited (no termination needed)
    with patch("subprocess.Popen") as popen_mock:
        proc_mock = popen_mock.return_value
        proc_mock.poll = MagicMock(side_effect=[None, None, None, 0, 0])
        proc_mock.terminate = MagicMock()
        proc_mock.returncode = 0

        job_src.job_submitted_event = MagicMock(
            is_set=MagicMock(side_effect=[False, True, True, True, True, True, True])
        )
        job_src.stop_event = MagicMock(
            is_set=MagicMock(side_effect=[False, True])
        )

        with patch("time.monotonic", side_effect=[0, 1, 1]):
            result = job_src._run_job()

        assert result is True
        proc_mock.terminate.assert_not_called()
        proc_mock.wait.assert_not_called()
        proc_mock.kill.assert_not_called()
