from dataclasses import dataclass
from tempfile import TemporaryFile
from threading import Event
from typing import TYPE_CHECKING
from subprocess import TimeoutExpired

import binascii
import random
import subprocess
import traceback
import time

from .logger import logger

if TYPE_CHECKING:
    from .mars import ConfigJobSource, ConfigDUT, ConfigDUTJobSource


@dataclass
class JobSource:
    JOB_SOURCE_NAME = "Unspecified"

    job_src: 'ConfigJobSource'
    db_dut: 'ConfigDUT'
    db_dut_job_src: 'ConfigDUTJobSource'

    def __post_init__(self):
        self.job_submitted_event = Event()
        self.stop_event = Event()

    def _setup_job(self) -> bool:
        """
        Can be implemented by the subclasses.

        WARNING: DO NOT DO ANY WORK HERE THAT WOULD LEAK RESOURCES IF THE PROCESS REBOOTS
        """
        return True

    def _try_cancel_job_pickup(self) -> bool:
        """
        Can be implemented by subclasses to attempt cancelling job pickup.
        Returns True if cancellation succeeded (no job picked up yet).
        Returns False if job is already picked up/busy (cancellation failed).
        """
        return False

    def _run_job(self) -> bool:  # pragma: nocover
        """
        Implemented by the subclasses.
        Attempts to run one job and then returns whether a job has run.
        """
        raise NotImplementedError

    def _runner_job_polling_complete(self) -> bool:
        """
        Can be implemented by subclasses to signal when the runner had
        the opportunity to pick any job that would have been queued
        since we last check.
        """
        return False

    def run_job(self) -> bool:
        """
        Run job using the subclass-provided `_run_job()` method, while
        automatically managing the job cookie.
        Returns the boolean returned by `_run_job()`.
        """
        if not self.job_src.expose_runners:
            return False
        if not self.db_dut_job_src.exposed:
            return False

        # Generate unique string representing this job source
        random_string = binascii.hexlify(random.randbytes(32)).decode()
        self.job_cookie = self.JOB_SOURCE_NAME + "_" + random_string

        try:
            ret = self._run_job()
        except Exception:
            traceback.print_exc()
            ret = False
        finally:
            # Reset the cookie now that the job is done executing
            self.job_cookie = None

        return ret

    def assert_job_from_us(self, job_cookie: str):
        """
        Assert that the passed-in job cookie does not match the current cookie for this job source
        """
        if job_cookie is None or self.job_cookie != job_cookie:
            raise ValueError("The job cookie doesn't match")

        self.job_submitted_event.set()


@dataclass
class JobSourceExternalCommand(JobSource):
    JOB_PICKUP_TIMEOUT_SECONDS = 20
    JOB_SUBMISSION_TIMEOUT_SECONDS = 45
    POLLING_SECONDS = 0.5

    def _subprocess_kwargs(self) -> dict[str, str]:  # pragma: nocover
        """
        Implemented by the subclasses.
        Compute the list of subprocess arguments needed to run the job source
        """
        raise NotImplementedError

    def _run_job(self) -> bool:
        def exec_time():
            return time.monotonic() - time_start

        if not self._setup_job():
            return False

        proc = None
        try:
            with TemporaryFile(mode='w+t') as output:
                time_start = time.monotonic()

                # TODO: Find a way to make sure that if a process was started by an earlier instance, it will not
                # be able to keep running by accident and thus lead to potentially two sources being active at
                # the same time
                proc = subprocess.Popen(**self._subprocess_kwargs(), stdout=output, stderr=output, text=True)

                # Phase 1: Wait for job pickup (runner gets work from job source)
                # This is interruptible by stop_event
                while (proc.poll() is None and
                       not self.job_submitted_event.is_set() and
                       not self._runner_job_polling_complete() and
                       exec_time() < self.JOB_PICKUP_TIMEOUT_SECONDS and
                       not self.stop_event.is_set()):
                    self.job_submitted_event.wait(self.POLLING_SECONDS)

                # Phase 1 timeout: Try to cancel job pickup if job not submitted yet
                if not self.job_submitted_event.is_set():
                    if self._try_cancel_job_pickup():
                        # Cancellation succeeded, no job was picked up
                        return False

                # Phase 2: Wait for job submission to CI-tron
                # This is NOT interruptable to maintain atomicity
                submission_start = time.monotonic()
                while (proc.poll() is None and
                       not self.job_submitted_event.is_set() and
                       time.monotonic() - submission_start < self.JOB_SUBMISSION_TIMEOUT_SECONDS):
                    self.job_submitted_event.wait(self.POLLING_SECONDS)

                # Display an error message if the process failed
                if proc.returncode not in [None, 0]:
                    output.seek(0)
                    logger.error(f"The job source exited with the return code {proc.returncode}:\n\n{output.read()}")

                # Kill the process if job submission did not happen
                if not self.job_submitted_event.is_set():
                    return False

                # The job has now started, wait for the command to complete, or the stop signal
                while proc.poll() is None and not self.stop_event.is_set():
                    self.stop_event.wait(self.POLLING_SECONDS)

            return self.job_submitted_event.is_set()
        finally:
            # If the above block exited, no job was submitted by the job source within the allocated time, and the job
            # source process has not finished yet, then it is time to kill it...
            if all([proc is not None and proc.poll() is None,  # The process has started and is still running
                    not self.job_submitted_event.is_set()]):   # No jobs were submitted by the job source

                # Try disabling the runner on the job source side before killing its process without warning
                self._try_cancel_job_pickup()

                # Politely ask the runner process to exit, so that it may perform some cleanup operations of its own
                proc.terminate()

                try:
                    # Give some time for the process to perform its cleanup operation before killing it if it failed
                    proc.wait(5)
                except TimeoutExpired:
                    proc.kill()
