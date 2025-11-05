#!/usr/bin/env python3

from dataclasses import asdict, fields
from datetime import datetime, timedelta
from functools import cached_property
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from ipaddress import ip_address
from threading import Thread, Event
from collections import namedtuple, defaultdict
from copy import deepcopy
from urllib.parse import urlsplit, urlparse
from enum import IntEnum

from pydantic import field_validator
from pydantic.dataclasses import dataclass

from .android.fastbootd import FastbootDevice
from .artifact.http import HttpArtifactCache, HttpFetchingMethod, StaleHttpArtifactException
from .artifact import ArtifactIOBase, AggregateArtifact
from .dut import JobRequest, DUTState, lock_fd, PduPortStats
from .mars import MarsDB
from .message import LogLevel, JobIOMessage, ControlMessage, SessionEndMessage, Message, MessageType
from .pdu import PDUPortState, PDU
from .message import JobStatus, ControlMessageTag
from .job import (
    ArtifactDeployment,
    CollectionOfLists,
    Deployment,
    DeploymentState,
    DhcpDeployment,
    Job,
    Timeout,
    split_host_port,
)
from .logger import logger
from .minioclient import MinioClient, MinIOPolicyStatement, generate_policy
from . import config
from .boots_db import BootsDB, BootsDbFastbootDevice, BootsDbDhcpDevice
from .tftpd import TftpRequestOpcode, TftpRequestHandler, TftpRequest
from .dhcpd import DhcpRequest

import subprocess
import traceback
import threading
import requests
import tempfile
import logging
import secrets
import random
import select
import string
import shutil
import socket
import struct
import fcntl
import flask
import json
import math
import time
import yaml
import sys
import os


# Constants
CONSOLE_DRAINING_DELAY = 1
BOOT_SEQUENCE_POWER_THRESHOLD_MULTIPLIER = 0.8


class JobConsoleState(IntEnum):
    CREATED = 0
    ACTIVE = 1
    DUT_DONE = 2
    TEAR_DOWN = 3
    OVER = 4


class JobConsole(Thread):
    def __init__(self, machine_id, client_endpoint,
                 client_version=None, log_level=LogLevel.INFO):
        super().__init__(name='ConsoleThread')

        self.dut_id = machine_id

        self.client_endpoint = client_endpoint
        self.console_patterns = None
        self.client_version = client_version
        self.log_level = log_level

        # Sockets
        if self.client_version:
            logger.info(f"Connecting to the client endpoint {self.client_endpoint}")
            self.client_sock = socket.create_connection((self.client_endpoint.host, self.client_endpoint.port))
        else:
            self.client_sock = None
        self.salad_sock = None

        # Job-long state
        self._state = JobConsoleState.CREATED
        self.start_time = None
        self.line_buffer = bytearray()
        self._user_session_state = dict()

        self.reset_per_boot_state()

    @property
    def machine_is_unfit_for_service(self):
        return self.console_patterns and self.console_patterns.machine_is_unfit_for_service

    @classmethod
    def salad_request(cls, dut_id):
        salad_url = f"{config.SALAD_URL}/api/v1/machine/{dut_id}"
        r = requests.get(salad_url)
        r.raise_for_status()
        return r.json()

    def connect_to_salad(self):
        parsed_url = urlsplit(config.SALAD_URL)
        machine = self.salad_request(self.dut_id)
        port = machine.get("tcp_port")

        return socket.create_connection((parsed_url.hostname, port))

    def salad_console_reset(self):
        self.log("Resetting the serial console")

        r = requests.post(f"{config.SALAD_URL}/api/v1/machine/{self.dut_id}/reset")
        if r.status_code == 200:
            self.log(" => Reset complete")
        elif r.status_code == 501:
            self.log(" => Reset not available")
        else:
            self.log(f" => Reset failure: {r.text}")

    def reset_per_boot_state(self):
        self.last_activity_from_machine = None
        self.last_activity_from_client = None

        if self.console_patterns:
            self.console_patterns.reset_per_boot_state()
            self.needs_reboot = self.console_patterns.needs_reboot

    def close_salad(self):
        if self.salad_sock:
            try:
                self.salad_sock.shutdown(socket.SHUT_RDWR)
                self.salad_sock.close()
            except OSError:
                pass

    def close_client(self):
        if self.client_version:
            try:
                self.client_sock.shutdown(socket.SHUT_RDWR)
                self.client_sock.close()
            except OSError:
                pass

    def close(self):
        self.set_state(JobConsoleState.OVER)

    @property
    def state(self):
        if self._state == JobConsoleState.ACTIVE:
            return self._state if self.is_alive() else JobConsoleState.OVER

        return self._state

    def set_state(self, state, **kwargs):
        prev_state = self._state
        if state < prev_state:
            raise ValueError("The state can only move forward")
        elif state == prev_state:
            return
        else:
            self._state = state

        self.log(f"Job console state changed from {prev_state.name} -> {state.name}\n")

        if state == JobConsoleState.ACTIVE:
            self.start_time = datetime.now()

        elif state == JobConsoleState.DUT_DONE:
            # Skip the entire tear-down if we do not have a client
            if not self.client_version:
                self.set_state(JobConsoleState.OVER)

        elif state == JobConsoleState.TEAR_DOWN:
            # Kill the connection to SALAD
            self.close_salad()

            # Notify the client
            if self.client_version:
                if self.client_version == 0:
                    self.log(f"<-- End of the session: {self.console_patterns.job_status} -->\n")
                elif self.client_version == 1:
                    try:
                        status = JobStatus.from_str(self.console_patterns.job_status)
                        SessionEndMessage.create(job_bucket=kwargs.get('job_bucket'),
                                                 joules_consumed=kwargs.get('joules_consumed'),
                                                 status=status).send(self.client_sock)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        traceback.print_exc()
                try:
                    self.client_sock.shutdown(socket.SHUT_WR)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    pass

        elif state == JobConsoleState.OVER:
            # Make sure the connections to SALAD and the client are killed
            self.close_salad()
            self.close_client()

    def start(self, console_patterns):
        self.console_patterns = console_patterns
        super().start()

    def match_console_patterns(self, line):
        patterns_matched = self.console_patterns.process_line(line)

        # Tell the user what happened
        if len(patterns_matched) > 0:
            self.log(f"^~~ Matched the following patterns: {', '.join(patterns_matched)}\n",
                     tag=ControlMessageTag.DUT_CONSOLE_PATTERN_MATCHED,
                     metadata={"patterns": list(patterns_matched),
                               "line": line.decode()})

        # Check if the state changed
        self.needs_reboot = self.console_patterns.needs_reboot

    def log(self, msg: str, log_level: LogLevel = LogLevel.INFO,
            tag: ControlMessageTag = ControlMessageTag.NO_TAG, metadata: dict = {}):
        # Ignore messages with a log level lower than the minimum set
        if log_level < self.log_level:
            return

        if self.start_time is not None:
            relative_time = (datetime.now() - self.start_time).total_seconds()
        else:
            relative_time = 0.0

        log_msg = f"+{relative_time:.3f}s: {msg}"
        logger.info(log_msg.rstrip("\r\n"))

        if self.client_version:
            try:
                if self.client_version == 0:
                    self.client_sock.send(log_msg.encode())
                elif self.client_version == 1:
                    ControlMessage.create(log_msg, severity=log_level,
                                          tag=tag, metadata=metadata).send(self.client_sock)
            except OSError:
                pass

    def stop(self):
        self.set_state(JobConsoleState.OVER)
        self.join()

    def send_dut_output_to_client(self, buf):
        if self.client_version:
            if self.client_version == 0:
                self.client_sock.send(buf)
            elif self.client_version == 1:
                JobIOMessage.create(buf).send(self.client_sock)

    def run(self):
        try:
            self.salad_sock = self.connect_to_salad()
            self.set_state(JobConsoleState.ACTIVE)
        except Exception:
            self.log(f"ERROR: Failed to connect to the SALAD server:\n{traceback.format_exc()}")
            self.close()

        while self.state < JobConsoleState.OVER:
            fds = []
            if self.state < JobConsoleState.TEAR_DOWN:
                fds.extend([self.salad_sock.fileno()])
            if self.client_version:
                fds.extend([self.client_sock.fileno()])

            # Make sure all the FDs are valid, or exit!
            if any([fd < 0 for fd in fds]):
                self.log("Found a negative fd, aborting!")
                self.close()

            rlist, _, _ = select.select(fds, [], [], 1.0)

            for fd in rlist:
                try:
                    if fd == self.salad_sock.fileno():
                        # DUT's stdout/err: Salad -> Client
                        buf = self.salad_sock.recv(8192)
                        if len(buf) == 0:
                            self.set_state(JobConsoleState.DUT_DONE)

                        # Process the output line by line
                        cur = 0
                        while True:
                            idx = buf.find(b'\n', cur)
                            if idx < 0:
                                break

                            # We have found a newline character, send the completed line to the DUT
                            end_of_line = buf[cur:idx+1]
                            cur = idx + 1
                            self.send_dut_output_to_client(end_of_line)

                            # Generate the complete line before running the console patterns by prepending the leftover
                            # bytes from the previous loop before resetting this buffer (since we have made use of the
                            # bytes).
                            full_line = self.line_buffer + end_of_line
                            self.line_buffer = bytearray()
                            logger.info(f"{self.dut_id} -> {bytes(full_line)}")

                            # Try to match the line
                            try:
                                self.match_console_patterns(full_line)
                            except Exception:
                                self.log(traceback.format_exc())

                        # Send the leftover bytes to the client so that it always has the most up-to-date view, while
                        # keeping a copy in the line buffer so that we may reconstitute the complete line next time we
                        # receive bytes from the DUT
                        self.line_buffer += buf[cur:]
                        self.send_dut_output_to_client(buf[cur:])

                        # Update the last console activity if we already had activity,
                        # or when we get the first newline character as serial
                        # consoles may sometimes send unwanted characters at power up
                        if self.last_activity_from_machine is not None or b'\n' in buf:
                            self.last_activity_from_machine = datetime.now()

                        # The message got forwarded, close the session if it ended
                        if self.console_patterns.session_has_ended:
                            self.set_state(JobConsoleState.DUT_DONE)

                    elif self.client_sock and fd == self.client_sock.fileno():
                        # DUT's stdin: Client -> Salad
                        if self.client_version == 0:
                            buf = self.client_sock.recv(8192)
                            if len(buf) == 0:
                                self.close()

                            # Forward to the salad
                            self.salad_sock.send(buf)
                        elif self.client_version == 1:
                            try:
                                msg = Message.next_message(self.client_sock)
                                if msg.msg_type == MessageType.JOB_IO:
                                    self.salad_sock.send(msg.buffer)
                            except EOFError:
                                # Do not warn when we are expecting the client to close its socket
                                if self.state < JobConsoleState.TEAR_DOWN:
                                    self.log(traceback.format_exc())

                                self.log("The client closed its connection")

                                # Clean up everything on our side
                                self.close()

                        self.last_activity_from_client = datetime.now()
                except (ConnectionResetError, BrokenPipeError, OSError):
                    self.log(traceback.format_exc())
                    self.close()
                except Exception:
                    logger.error(traceback.format_exc())


class JobBucket:
    Credentials = namedtuple('Credentials', ['username', 'password', 'policy_name'])

    def __init__(self, minio, bucket_name, initial_state_tarball_file=None,
                 hostname_by_role={}):
        self.minio = minio
        self.name = bucket_name
        self.hostname_by_role = hostname_by_role

        self._credentials = dict()

        if initial_state_tarball_file:
            self.initial_state_tarball_file = tempfile.NamedTemporaryFile("w+b")
            shutil.copyfileobj(initial_state_tarball_file, self.initial_state_tarball_file)
            self.initial_state_tarball_file.seek(0)
        else:
            self.initial_state_tarball_file = None

        # Ensure the bucket doesn't already exist
        if not self.minio.bucket_exists(bucket_name):
            self.minio.make_bucket(bucket_name)
        else:
            raise ValueError("The bucket already exists")

    def remove(self):
        if self.minio.bucket_exists(self.name):
            self.minio.remove_bucket(self.name)

        for credentials in self._credentials.values():
            self.minio.remove_user_policy(credentials.policy_name, credentials.username)
            self.minio.remove_user(credentials.username)
        self._credentials = {}

    def __del__(self):
        try:
            self.remove()
        except Exception:
            traceback.print_exc()

    def credentials(self, role):
        return self._credentials.get(role)

    def create_owner_credentials(self, role, user_name=None, password=None,
                                 groups=None, whitelisted_ips=None):
        if user_name is None:
            user_name = f"{self.name}-{role}"

        if password is None:
            password = secrets.token_hex(16)

        if groups is None:
            groups = []

        if whitelisted_ips is None:
            whitelisted_ips = []

        policy_name = f"policy_{user_name}"

        self.minio.add_user(user_name, password)

        policy_statements = [
            MinIOPolicyStatement(buckets=[self.name], source_ips=whitelisted_ips)
        ]
        if len(whitelisted_ips) > 0:
            restrict_to_whitelisted_ips = MinIOPolicyStatement(allow=False, not_source_ips=whitelisted_ips)
            policy_statements.append(restrict_to_whitelisted_ips)
        policy = json.dumps(generate_policy(policy_statements))
        logger.debug(f"Applying the MinIO policy: {policy}")

        try:
            self.minio.apply_user_policy(policy_name, user_name, policy_statements)
        except Exception as e:
            self.minio.remove_user(user_name)
            raise e from None

        # Add the user to the wanted list of groups
        for group_name in groups:
            self.minio.add_user_to_group(user_name, group_name)

        credentials = self.Credentials(user_name, password, policy_name)
        self._credentials[role] = credentials

        return credentials

    def setup(self):
        if self.initial_state_tarball_file:
            self.minio.extract_archive(self.initial_state_tarball_file, self.name)
            self.initial_state_tarball_file.close()

    def access_url(self, role=None):
        endpoint = urlparse(self.minio.url)

        role_creds = self.credentials(role)
        if role_creds:
            credentials = f"{role_creds[0]}:{role_creds[1]}@"
        else:
            credentials = ""

        hostname = self.hostname_by_role.get(role, endpoint.hostname)
        return f'{endpoint.scheme}://{credentials}{hostname}:{endpoint.port}'

    @classmethod
    def from_job_request(cls, minio, request, machine):
        # Look for the HOST header, to get the hostname used by the client to connect to
        # the executor, so that we can use the same host when telling the client how to
        # download shared folder
        hostname_by_role = {}
        for name, value in request.http_headers.items():
            if name.lower() == "host":
                if len(value) > 0:
                    hostname_by_role["client"] = value.split(":")[0]

        # Convert the job_bucket_initial_state_tarball_file_fd to a file-like object
        if request.job_bucket_initial_state_tarball_file_fd > 0:
            initial_state_tarball_file = os.fdopen(request.job_bucket_initial_state_tarball_file_fd, "rb")
        else:
            initial_state_tarball_file = None

        last_exception = None
        for i in range(5):
            # Make sure the fixed part of the bucket name isn't filling up the whole bucket name (64 chars max)
            base_bucket_name = f"job-{machine.id}-{request.job_id}"[0:56]

            # Append up to 32 characters of entropy within the bucket name limits of minio:
            # Bucket names can consist only of lowercase letters, numbers, dots (.), and hyphens (-)
            # We however do not allow dots, as the following sequence is not allowed: .., .-, and -.
            rnd = ''.join(random.choice(string.ascii_lowercase + string.digits + '-') for i in range(32))

            try:
                bucket_name = MinioClient.create_valid_bucket_name(f"{base_bucket_name}-{rnd}")

                return cls(minio, bucket_name=bucket_name,
                           initial_state_tarball_file=initial_state_tarball_file,
                           hostname_by_role=hostname_by_role)
            except ValueError as e:
                last_exception = e

        raise last_exception from None


class ExecutorHttpArtifactCache(HttpArtifactCache):
    def __init__(self, executor: "Executor"):
        self.executor = executor

        super().__init__(config.EXECUTOR_ARTIFACT_CACHE_ROOT, log_callback=executor.log, start_bg_validation=True)

    @property
    def common_template_resources(self):
        return self.executor.common_template_resources

    def cache_deployment(self, deployment: Deployment | DeploymentState, polling_delay: float = 0.05,
                         wait_for_completion=True, timeout: Timeout = Timeout()) -> bool:

        log = self.executor.log

        # Start the download of all the artifacts
        pending_artifacts = set()
        for url, paths in deployment.artifacts.items():
            # Use the first path referencing this URL as a name
            artifact_path = list(paths.keys())[0]
            job_artifact = paths[artifact_path]
            name = JobArtifactBaseRequestHandler.path_from_artifact_path(*artifact_path)

            # Ignore data artifacts
            if not url:
                continue

            # Ignore url artifacts that need url rewriting
            if job_artifact.has_dynamic_url:
                continue

            # Try to get the artifact from our instance cache, or acquire a new instance
            with self.cached_artifacts_lck:
                artifact = self.cached_artifacts.get(url)
            if artifact:
                log(f"Re-using [{name}]({url}) from our artifact cache\n")
            else:
                log(f'Caching [{name}]({url}) into our artifact cache...\n')
                artifact = self.get_or_reuse_artifact(url=url, name=name)
                pending_artifacts.add(artifact)

        if wait_for_completion:
            # Wait for all pending artifacts to complete
            retry_cnt = defaultdict(int)
            max_retries = 3
            while len(pending_artifacts) > 0 and not timeout.has_expired:
                for artifact in set(pending_artifacts):
                    if not artifact.is_instance_available:
                        continue

                    instance = artifact.get_instance()
                    try:
                        if instance.is_complete:
                            pending_artifacts.remove(artifact)

                            # Compute the download speed
                            size_mb = os.stat(instance.get_filepath()).st_size / 1024**2
                            if total_time := instance.completion_time:
                                # Compute the average download speed
                                avg_speed = round(size_mb / total_time, 2)
                            else:
                                avg_speed = "???"

                            fetch_method = instance.fetch_method.name
                            msg = f"Fetched {instance.name} through {fetch_method} ({round(size_mb, 2)} MiB)"
                            if fetch_method == HttpFetchingMethod.FULL_DOWNLOAD:
                                resumes = instance.resume_count
                                msg += f": Took {round(total_time, 1)}s ({avg_speed} MiB/s) and {resumes} resumes"
                            log(msg)
                    except StaleHttpArtifactException:
                        # The artifact got stale mid-way through the download,
                        # remove it from our pending list then create a new one
                        # and restart the download
                        if retry_cnt[instance] < max_retries:
                            retry_cnt[instance] += 1
                            log(f"Restarting caching [{name}]({url}) into our cache "
                                f"(attempt {retry_cnt[instance]}/{max_retries})...\n")
                            pending_artifacts.remove(artifact)
                            pending_artifacts.add(self.__create_artifact(url=instance.url, name=instance.name))
                        else:
                            log(f"Failed to cache [{name}]({url}) too many times, aborting!\n")
                            self.executor.job_console.set_state(JobConsoleState.OVER)

                time.sleep(polling_delay)

            return len(pending_artifacts) == 0
        else:
            return True

    def prune_artifacts(self, unused_for_days: timedelta = timedelta(days=60)):
        log = self.executor.log

        log(f"Pruning artifacts that were unused for {unused_for_days} days")

        r = super().prune_artifacts(unused_for_days)

        log(f"  --> Pruned {r.pruned}/{r.found} artifacts ({r.total_MiB:.2f} MiB) in {r.total_seconds:.2f} seconds "
            f"(errors={r.error})")


class JobArtifactBaseRequestHandler:
    ARTIFACT_BY_PATH_PREFIX = "/_/job/"

    @classmethod
    def path_from_artifact_path(cls, *artifact_path: str):
        return cls.ARTIFACT_BY_PATH_PREFIX + "/".join(artifact_path)

    def log_message(self, msg):
        self.executor.log(msg)

    @property
    def job_artifacts(self):
        raise NotImplementedError()

    def open_artifact_by_path(self, path: str, artifact_cache: HttpArtifactCache) -> ArtifactIOBase:
        # Ensure the path starts with a /
        if not path.startswith("/"):
            path = f"/{path}"

        if path.startswith(self.ARTIFACT_BY_PATH_PREFIX):
            # The path points to an artifact by path in the job description (ie. /start/kernel)
            artifacts = []
            for _, paths in self.executor.get_current_deployment().artifacts.items():
                for artifact_path, artifact in paths.items():
                    artifact_path = self.path_from_artifact_path(*artifact_path)
                    if artifact_path.startswith(path):
                        artifacts.append(artifact.open(path, artifact_cache=artifact_cache))

            return AggregateArtifact(artifacts)
        elif self.job_artifacts:
            # The path is provided by deployment.storage

            # Generate the list of paths, with the following priorities:
            # 1. Uncategorised paths first, since they are the last defined
            # 2. Categories, sorted by name
            artifacts = deepcopy(self.job_artifacts.uncategorised)
            for k in sorted(self.job_artifacts.categories.keys()):
                artifacts.extend(self.job_artifacts.categories[k])

            # Look through the sorted artifacts to find a match for the path
            for artifact in artifacts:
                if artifact.matches(path):
                    return artifact.open(path, artifact_cache=artifact_cache)


class JobHTTPServerRequestHandler(BaseHTTPRequestHandler, JobArtifactBaseRequestHandler):
    @property
    def executor(self):
        return self.server.executor

    @property
    def job_artifacts(self):
        if deployment := self.server.executor.get_current_deployment():
            if deployment.storage:
                return deployment.storage.http
        return CollectionOfLists()

    def stream_artifact(self, f: ArtifactIOBase, headers_only=False):
        response = 200
        if self.headers.get("If-None-Match") == f.etag:
            response = 304

        self.send_response(response)
        self.send_header("Content-Type", f.content_type or "application/octet-stream")
        self.send_header("Transfer-Encoding", "chunked")  # We may not know the size yet, so let's just stream it!

        # Make sure the client always tells us when it accesses the file, so
        # that we can log every access to the resource
        self.send_header("CacheControl", "max-age=0, no-cache, must-revalidate")
        self.send_header("ETag", f.etag)
        self.end_headers()

        if not headers_only and response == 200:
            for chunk in f.stream():
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")

            # Signal the end of file
            self.wfile.write("0\r\n\r\n".encode())

    def _is_request_from_dut(self):
        # Allow requests coming through the proxy as they are already validated
        # as coming from the DUT.
        if self.client_address[0] == self.server.server_address[0]:
            return True

        # Restrict access to the job's artifacts to the DUT that is supposed to access them
        # While restricting access by IP isn't foolproof, it makes it harder for potential
        # attackers to figure out if they are talking to the right HTTP server. To this end,
        # we also do not use the error code 403 so as to make it less clear what is going on
        dut_ip_address = self.server.executor.db_dut.ip_address
        if self.client_address[0] == dut_ip_address:
            return True

        self.log_message("WARNING: Got an HTTP query from an unexpected IP address "
                         "(%s instead of %s)", self.client_address[0], dut_ip_address)
        return False

    def handle_request(self, headers_only=False):
        # Let's close the connection after every transaction
        self.close_connection = True

        try:
            if not self._is_request_from_dut():
                return self.send_error(404)

            # Remove any potential GET parameter
            path = self.path.split('?')[0]

            if artifact := self.open_artifact_by_path(path, artifact_cache=self.server.executor.artifact_cache):
                return self.stream_artifact(artifact, headers_only=headers_only)
            else:
                self.log_message("ERROR: artifact not found: %s", path)
                return self.send_error(404)
        except Exception:
            self.log_message("ERROR: Caught an exception:\n%s", traceback.format_exc())
            return self.send_error(500)

    def do_GET(self):
        self.handle_request(headers_only=False)

    def do_HEAD(self):
        self.handle_request(headers_only=True)

    # https://httpwg.org/specs/rfc9110.html#CONNECT
    def do_CONNECT(self):
        if not self._is_request_from_dut():
            return self.send_error(405)

        # Validate the syntax of the target of the proxy request
        try:
            target_host, target_port = split_host_port(self.path)
        except ValueError as exc:
            self.log_error(f"ERROR: Invalid host:port `{self.path}`: {str(exc)}")
            return self.send_error(400)

        msg_prefix = f"[PROXY] Connecting to {target_host}:{target_port}:"

        try:
            valid_target_host = self.validate_endpoint(msg_prefix, target_host, target_port)
            if not valid_target_host:
                return self.send_error(405)  # Method Not Allowed, to not give away that it might work for other targets

            target_connection = socket.create_connection(
                (valid_target_host, target_port),
                timeout=self.timeout,
            )
        except Exception as exc:
            self.log_error(f"{msg_prefix} failed: {str(exc)}")
            return self.send_error(502)

        self.send_response(200, "Connection Established")
        self.end_headers()

        # And we're done, the rest is simply to copy the bytes back and forth
        CPU_PAGE_SIZE = os.sysconf('SC_PAGESIZE')
        buffer = bytearray(16 * CPU_PAGE_SIZE)
        while True:
            rlist, wlist, xlist = select.select(
                [self.connection, target_connection],
                [],
                [self.connection, target_connection],
                self.timeout
            )
            if xlist or not rlist:
                break
            for r in rlist:
                bytes_received = r.recv_into(buffer)
                if bytes_received == 0:
                    return
                if r is self.connection:
                    target_connection.sendall(buffer[:bytes_received])
                else:
                    self.connection.sendall(buffer[:bytes_received])

    def validate_endpoint(self, msg_prefix: str, target_host: str, target_port: int) -> bool:
        # Connecting to the gateway itself is always allowed, so let's see if
        # target_host is the gateway
        gateway_ip = self.server.server_address[0]
        # Note: resolving our own name returns a loopback address, while resolving
        # our ip address returns itself
        _, _, target_ipaddrlist = socket.gethostbyname_ex(target_host)
        if target_host == gateway_ip or any(ip_address(ip).is_loopback for ip in target_ipaddrlist):
            self.executor.log(f"{msg_prefix} access to ci-gateway granted")
            return gateway_ip

        target = f"{target_host}:{target_port}"

        # Check against the endpoints declared by the job
        endpoints_in_job = self.server.executor.job_config.proxy.allowed_endpoints or []
        if target not in endpoints_in_job:
            self.executor.log(f"{msg_prefix} access refused by the job "
                              "(see `CI_TRON_PROXY__ALLOWED_ENDPOINTS` in the documentation).",
                              log_level=LogLevel.ERROR)
            self.log_error(f"Job only declares needing the following endpoints: {endpoints_in_job}")
            return None

        # Check against the endpoints listed in mars_db
        endpoints_in_config = self.server.executor.mars_db.jobs.proxy.allowed_endpoints or []
        if target not in endpoints_in_config:
            self.executor.log(f"{msg_prefix} access refused by the farm admin.",
                              log_level=LogLevel.ERROR)
            self.log_error(f"MarsDB only allows the following endpoints: {endpoints_in_config}")
            return None

        self.executor.log(f"{msg_prefix} access granted")
        return target_host


class JobHTTPServer(ThreadingHTTPServer):
    @classmethod
    def __iface_query_param(cls, iface, param):
        # Implementation from:
        # https://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                return socket.inet_ntop(socket.AF_INET,
                                        fcntl.ioctl(s.fileno(), param,
                                                    struct.pack('256s',
                                                                iface.encode('utf8'))
                                                    )[20:24])
            except OSError:
                # Iface doesn't exist, or no IP assigned
                raise ValueError(f"The interface {iface} has no IP assigned") from None

    def __init__(self, executor):
        self.executor = executor

        # Only expose the server to private interface, if set
        host = ""
        if config.PRIVATE_INTERFACE:
            try:
                host = self.__iface_query_param(config.PRIVATE_INTERFACE, 0x8915)  # SIOCGIFADDR
            except Exception:
                self.executor.log(("WARNING: Failed to get the IP address of the private interface:\n"
                                   f"{traceback.format_exc()}"))

        super().__init__((host, 0), JobHTTPServerRequestHandler)
        threading.Thread(target=self.serve_forever, name="HTTP", daemon=True).start()

    @property
    def url(self):
        host, port = self.server_address
        return f"http://{host}:{port}"

    def path_to(self, *args):
        local_path = JobHTTPServerRequestHandler.path_from_artifact_path(*args)
        return f"{self.url}{local_path}"


class JobTftpRequestHandler(TftpRequestHandler, JobArtifactBaseRequestHandler):
    def __init__(self, executor: "Executor", new_client: TftpRequest, *args, **kwargs):
        # Try to match the request to a job artifact before starting handling
        # the request as it may raise
        self.executor = executor
        self.artifact = self.get_file_handle(executor, new_client)

        # Create the request handler
        TftpRequestHandler.__init__(self, new_client, *args, **kwargs)

    def get_file_handle(self, executor: "Executor", request: TftpRequest):
        # Restrict access to the job's artifacts to the DUT that is supposed to access them
        # While restricting access by IP isn't foolproof, it makes it harder for potential
        # attackers to figure out if they are talking to the right TFTP server.
        dut_ip_address = executor.db_dut.ip_address
        if request.client_address != dut_ip_address:
            error_msg = "Got a TFTP query from an unexpected IP address " \
                        f"({request.client_address} instead of {dut_ip_address})"
            raise ValueError(error_msg)

        # Make sure we are getting a read request, as we do not support writes
        if request.opcode != TftpRequestOpcode.RRQ:
            raise ValueError("Only read requests are supported")

        # Make sure the request is of the right type
        if request.filemode != 'octet':
            raise ValueError(f"Mode {request.filemode} not supported")

        if artifact := self.open_artifact_by_path(request.filename, artifact_cache=self.executor.artifact_cache):
            return artifact
        else:
            raise ValueError("Unknown filename")

    @property
    def job_artifacts(self):
        if deployment := self.executor.get_current_deployment():
            if deployment.storage:
                return deployment.storage.tftp
        return CollectionOfLists()

    def load_file(self, filename):
        try:
            self.filename = filename
            self.fh = self.artifact
            self.fh.seek(0, os.SEEK_END)
            self.filesize = self.fh.tell()
            self.fh.seek(0, os.SEEK_SET)

            return True
        except Exception:
            self.log_message(f"ERROR: Caught an exception:\n{traceback.format_exc()}")

        return False

    @classmethod
    def path_to(cls, *args):
        return JobArtifactBaseRequestHandler.path_from_artifact_path(*args).removeprefix("/")


class Executor(Thread):
    def __init__(self, mars_db, db_dut, job_request):
        self.mars_db = mars_db
        self.db_dut = db_dut
        self.job_request = job_request

        self.state = DUTState.QUEUED
        self.job_console = None
        self.bootsdb_default_deployment = DeploymentState()
        self.cur_deployment = None
        self.stop_event = Event()
        self.firmware_boot_complete_event = Event()

        self.pulled_container_images = defaultdict(dict)
        self.nbd_servers = dict()

        # Statistics
        self.pdu_port_start_energy = None

    @cached_property
    def minio(self):
        return MinioClient()

    @cached_property
    def job_bucket(self):
        job_bucket = JobBucket.from_job_request(self.minio, self.job_request, self.db_dut)
        if job_bucket:
            job_bucket.create_owner_credentials("dut", groups=self.job_request.minio_groups,
                                                whitelisted_ips=[f'{self.db_dut.ip_address}/32'])
        return job_bucket

    @cached_property
    def job_httpd(self):
        return JobHTTPServer(self)

    @property
    def common_template_resources(self) -> dict[str, str]:
        template_params = {
            **Job.common_template_resources(),
            "job": {
                "bucket": {
                    "url": self.job_bucket.minio.url,
                    "name": self.job_bucket.name,
                    "access_key": self.job_bucket.credentials('dut').username,
                    "secret_key": self.job_bucket.credentials('dut').password,
                },
                # Get the current deployment, without rendering any template so that we avoid circular dependencies
                "deployment": self.get_current_deployment(),
                "http": {
                    "path_to": lambda p: self.job_httpd.path_to(p),
                    "url": self.job_httpd.url,
                },
                "tftp": {
                    "path_to": lambda p: JobTftpRequestHandler.path_to(p),
                    # TODO: Add URL here?
                },
                "imagestore": self.pulled_container_images,
                "nbd": self.nbd_servers,
            },
            "dut": self.db_dut.safe_attributes,
            "environ": self.job_request.environ,
        }

        # Fix up the kernel cmdline now that we have the resources to render them
        template_params["job"]["deployment"] = self.get_current_deployment(template_params=template_params)

        return template_params

    @cached_property
    def job_config(self):
        job_resources = self.common_template_resources
        raw_job = self.job_request.raw_job
        if self.job_request.job_url:
            self.log("Downloading the job description template")
            instance = self.artifact_cache.get_or_reuse_instance(self.job_request.job_url, "job.yml.j2")
            raw_job = instance.open().read().decode()
        rendered_str = Job.render_template_with_resources(raw_job, self.db_dut, self.job_bucket,
                                                          **job_resources)

        # Sanitize the rendered job string to reduce the chances of accidentally leaking an important secret
        r = job_resources
        sanitized_rendered_str = rendered_str
        for secret in ([r["job"]["bucket"]["secret_key"]] +
                       [v for k, v in r["environ"].items() if "_TOKEN" in k or "_PASSWORD" in k]):
            sanitized_rendered_str = sanitized_rendered_str.replace(secret, '[MASKED]')

        # Show the sanitized rendered job, for users to inspect
        self.log(f"Executing the following job:\n{sanitized_rendered_str}")

        return Job.render_with_resources(rendered_str, self.db_dut, self.job_bucket, render_job_template=False,
                                         **job_resources)

    @cached_property
    def pdu_port(self):
        start = time.monotonic()

        config_pdu = self.mars_db.pdus.get(self.db_dut.pdu)
        if config_pdu is None:
            return None

        if pdu := PDU.create(config_pdu.driver, config_pdu.name, config_pdu.config, config_pdu.reserved_port_ids):
            for port in pdu.ports:
                if str(port.port_id) == str(self.db_dut.pdu_port_id):
                    port.min_off_time = self.db_dut.pdu_off_delay

                    exec_time = (time.monotonic() - start) * 1000
                    self.log(f"Initialized the PDU port in {exec_time:.1f} ms\n")

                    return port

            raise ValueError('Could not find a matching port for %s on %s' % (self.db_dut.pdu_port_id, pdu))

        raise ValueError("Could not create the PDU")

    @cached_property
    def artifact_cache(self):
        return ExecutorHttpArtifactCache(executor=self)

    def get_current_deployment(self, template_params=None):
        """ Returns the current deployment, after being combined with the bootsdb default deployment """

        deployment = DeploymentState().update(self.bootsdb_default_deployment)
        if self.cur_deployment:
            deployment = deployment.update(self.cur_deployment)

        if template_params and deployment.kernel:
            deployment.kernel.cmdline = ArtifactDeployment.render_data_template(self.artifact_cache,
                                                                                data=str(deployment.kernel.cmdline),
                                                                                template_params=template_params)

        return deployment

    def cache_deployment(self, deployment=None, wait_for_completion=True, timeout: Timeout = Timeout()) -> bool:
        # Run the function in the background if asked not to wait for the completion
        if not wait_for_completion:
            threading.Thread(target=self.cache_deployment, kwargs={"deployment": deployment,
                                                                   "wait_for_completion": True,
                                                                   "timeout": timeout})
            return

        if deployment is None:
            deployment = self.get_current_deployment()

        if not self.artifact_cache.cache_deployment(deployment, wait_for_completion=wait_for_completion,
                                                    timeout=timeout) or timeout.has_expired:
            return False

        # Figure out the list of container images that have not been pulled before
        to_pull = set()
        for imgstore_name, imgstore in deployment.container_images.items():
            for img_name, img in imgstore.items():
                # Only pull the images that have not been
                if img_name not in self.pulled_container_images[imgstore_name]:
                    self.pulled_container_images[imgstore_name][img_name] = img
                    to_pull.add(img)

        # Pull all the wanted images that have not been pulled before
        if len(to_pull) > 0:
            self.log(f"Pulling {len(to_pull)} container image(s):")
            for i, img in enumerate(to_pull):
                try:
                    msg = f"Pulling {img.image_name} ({img.platform}) in the {img.store_name} store..."
                    self.log(f" * [{i+1}/{len(to_pull)}] {msg}")
                    img.pull(timeout=timeout.remaining_time.total_seconds())
                    self.log(f"   --> Using image ID {img.image_id}")
                except ValueError as e:
                    self.log(f"   --> {str(e)}", log_level=LogLevel.ERROR)
                except subprocess.TimeoutExpired:
                    self.log("   --> Timeout!", log_level=LogLevel.ERROR)
                    return False

        # Setup all the NBD drives
        nbd_to_setup = {key: value for key, value in deployment.nbd_storages.items() if key not in self.nbd_servers}
        self.log(f"Setting up {len(nbd_to_setup)} NBD server(s)")
        for i, name in enumerate(nbd_to_setup):
            nbd = nbd_to_setup[name]
            self.log(f" * [{i+1}/{len(nbd_to_setup)}] Setting up '{name}'")
            try:
                self.nbd_servers[name] = nbd.setup(name=f"nbd-{name}", artifact_cache=self.artifact_cache,
                                                   timeout=timeout.remaining_time.total_seconds())
            except subprocess.TimeoutExpired:
                return False

        return True

    def cancel_job(self):
        self.log("WARNING: The job got cancelled at the infra admin's request\n")
        self.stop_event.set()

    def log(self, msg: str, log_level: LogLevel = LogLevel.INFO,
            tag: ControlMessageTag = ControlMessageTag.NO_TAG, metadata: dict = {}):
        if not msg:
            return

        if not msg.endswith("\n"):
            msg += "\n"

        if self.job_console is not None:
            self.job_console.log(msg, log_level=log_level, tag=tag, metadata=metadata)

    def _update_bootsdb_device(self, dev_type: str, device_name, device):
        for path in [config.BOOTS_DB_USER_FILE, config.BOOTS_DB_FILE]:
            if path and os.path.isfile(path):
                try:
                    db = BootsDB.from_path(path, **{device_name: device},
                                           **self.common_template_resources)
                except Exception:
                    self.log(f"WARNING: Could not parse the BOOTS DB file '{path}':\n{traceback.format_exc()}")
                    continue

                for boots_name, boots_dev in getattr(db, dev_type).items():
                    if boots_dev.match.matches(device):
                        boots_dev.name = boots_name

                        if self.bootsdb_default_deployment != boots_dev.defaults:
                            self.log(f"Using BootsDB's {boots_name} defaults")
                            self.bootsdb_default_deployment = boots_dev.defaults

                            # Make sure all the artifacts that would be brought by the change
                            # of defaults get cached before the DUT requests them
                            self.cache_deployment(wait_for_completion=False)

                        return boots_dev

    def update_bootsdb_defaults_from_fbdev(self, fbdev: FastbootDevice) -> BootsDbFastbootDevice:
        return self._update_bootsdb_device("fastboot", "fbdev", fbdev)

    def update_bootsdb_defaults_from_dhcp_request(self, request: DhcpRequest) -> BootsDbDhcpDevice:
        return self._update_bootsdb_device("dhcp", "dhcp_request", request)

    def handle_fastboot_device_added(self):
        def open_artifact(job_artifacts: ArtifactDeployment | CollectionOfLists[ArtifactDeployment],
                          path: str, invalid: list[str]):
            if not isinstance(job_artifacts, CollectionOfLists):
                job_artifacts = [job_artifacts]

            artifacts = []
            for i, job_artifact in enumerate(job_artifacts):
                try:
                    subartifact_path = f"{path}/{i}"
                    artifact = job_artifact.open(path=subartifact_path, artifact_cache=self.artifact_cache)
                    if artifact.filesize > 0:
                        artifacts.append(artifact)
                except Exception:
                    self.log(f"ERROR: Failed to open the {path} artifact:\n{traceback.format_exc()}")

            if len(artifacts) != len(job_artifacts):
                # The artifact could not be open or is empty, so mark it as invalid
                invalid.append(path)
            else:
                return AggregateArtifact(artifacts)

        def boot(boot_img):
            # Reset the boot counter to avoid boot issues
            self.log("Selecting the slot A for boot")
            try:
                fbdev.run_cmd("set_active", "a")
            except Exception as e:
                self.log(f"--> {e}")

            # Upload the generated boot image and run it
            self.log("Uploading the boot image")
            fbdev.upload(boot_img)

            # Booting the image
            self.log("Booting the image")
            fbdev.boot()

        # Create the fastboot device by enumerating USB devices and matching the one with the right serial number
        fbdev = FastbootDevice.from_serial(self.db_dut.id)
        if not fbdev:
            raise ValueError(f"Could not find the Fastboot device with serial {self.db_dut.id}")

        # Consider the firmware boot process complete
        self.firmware_boot_complete_event.set()

        # Try matching the fastboot device to our BootsDB database
        self.update_bootsdb_defaults_from_fbdev(fbdev)

        if deployment := self.get_current_deployment(template_params=self.common_template_resources):
            # Make sure all the files we need are cached and ready to use
            self.cache_deployment(deployment)

            # Open the artifacts for immediate use
            # NOTE: We append the DTBs to the kernel image, as is expected by up to Android 9
            # Source: https://source.android.com/docs/core/architecture/bootloader/dtb-images
            invalid_artifacts = []
            kernel_artifact = AggregateArtifact([open_artifact(deployment.kernel, "kernel", invalid_artifacts),
                                                 open_artifact(deployment.dtb, "dtb", [])])
            initrd_artifact = open_artifact(deployment.initramfs, "initramfs", invalid_artifacts)
            dtb_artifact = open_artifact(deployment.dtb, "dtb", invalid_artifacts)
            boot_img_artifact = None
            if deployment.fastboot and deployment.fastboot.boot_image:
                boot_img_artifact = open_artifact(deployment.fastboot.boot_image, "boot_image", invalid_artifacts)

            # Make sure all the artifacts
            if len(invalid_artifacts) > 0:
                self.log(f"ERROR: The following artifacts are either empty or missing: {', '.join(invalid_artifacts)}")
                self.job_console.set_state(JobConsoleState.OVER)
                return

            # Boot the provided boot image, if present. Otherwise, build it!
            if boot_img_artifact:
                boot(boot_img_artifact)
            else:
                with tempfile.NamedTemporaryFile() as output:
                    args = [sys.executable, "-m", "valve_gfx_ci.executor.server.android.mkbootimg",
                            "--kernel", kernel_artifact.filepath,
                            "--cmdline", str(deployment.kernel.cmdline),
                            "--ramdisk", initrd_artifact.filepath,
                            "--dtb", dtb_artifact.filepath]

                    if fastboot_cfg := deployment.fastboot:
                        for field, value in fastboot_cfg.fields_set.items():
                            args += [f"--{field}", str(value)]

                    args += ["--output", output.name]

                    self.log(f"Generating a boot image using the following parameters: {args}")
                    subprocess.check_call(args, stdout=sys.stderr, stderr=sys.stderr)

                    output.seek(0, os.SEEK_SET)
                    boot(output)

    def update_mars_fields(self, **fields):
        server_url = f"http://localhost:{config.EXECUTOR_PORT}/api/v1/dut/{self.db_dut.id}"
        r = requests.patch(server_url, json=fields)

        if r.status_code != 200:
            logger.error(f"ERROR: Failed to update the MaRS fields associated to this DUT. Reason: {r.text}")

    def queue_quick_check(self):
        r = requests.post(f"http://localhost:{config.EXECUTOR_PORT}/api/v1/dut/{self.db_dut.id}/quick_check")
        if r.status_code != 200:
            logger.error(f"ERROR: Failed to queue a quick check on the DUT. Reason: {r.text}")

    def firmware_boot_completed(self, completion_time: timedelta):
        self.log(f"Firmware boot sequence complete. Took {completion_time.seconds:.1f} s\n",
                 tag=ControlMessageTag.DUT_FIRMWARE_BOOT_COMPLETE)

        if self.db_dut.firmware_boot_time is None or completion_time.total_seconds() > self.db_dut.firmware_boot_time:
            self.log(" --> Exceeded the known boot time, updating the MaRS database\n")
            self.update_mars_fields(firmware_boot_time=math.ceil(completion_time.total_seconds()))

        # Update the average boot power usage, if the average boot power we
        # calculated is more than 10% off from the MaRSDB value
        if len(self.boot_pwr_samples) > 0:
            avg_boot_power = round(sum(self.boot_pwr_samples) / len(self.boot_pwr_samples), 1)
            if avg_boot_power and (self.db_dut.boot_sequence_power is None or
                                   abs(avg_boot_power - self.db_dut.boot_sequence_power) / avg_boot_power > 0.1):
                self.update_mars_fields(boot_sequence_power=avg_boot_power)

    def get_pdu_port_power_energy(self) -> (float | None, float | None):
        # NOTE: Rather than polling the PDU port, let's query the energy/power
        # straight from the executor server. This is faster, and more likely to
        # yield a usable energy since the server implements it in software if
        # the pdu port doesn't support it.
        port = self.pdu_port
        try:
            r = requests.get(f"http://localhost:{config.EXECUTOR_PORT}/api/v1/pdu/{port.pdu.name}/port/{port.port_id}")
            if r.status_code == 200:
                json = r.json()
                return json.get("instant_power"), json.get("energy")
        except Exception:
            traceback.print_exc()

        return None, None

    @property
    def joules_consumed(self) -> float | None:
        _, cur_energy = self.get_pdu_port_power_energy()
        if self.pdu_port_start_energy is not None and cur_energy is not None:
            return cur_energy - self.pdu_port_start_energy

    def start_session(self):
        # Connect to the client's endpoint, to relay the serial console
        self.job_console = JobConsole(self.db_dut.id,
                                      client_endpoint=self.job_request.callback_endpoint,
                                      client_version=self.job_request.version)

    def run(self):
        def session_end():
            # Ensure we cut the power to the DUT
            self.pdu_port.set(PDUPortState.OFF)

            # Clean up the artifact cache directory
            self.artifact_cache.prune_artifacts()

            # Shut down the NBD servers
            if len(self.nbd_servers) > 0:
                self.log(f"Shutting down {len(self.nbd_servers)} NBD server(s):")
                for i, nbd in enumerate(self.nbd_servers.values()):
                    self.log(f" * [{i+1}/{len(self.nbd_servers)}] Tearing down '{nbd.name}'")
                    nbd.teardown()

            self.job_console.close()
            self.job_console = None
            self.cur_deployment = None
            if self.job_bucket:
                self.job_bucket.remove()
                self.job_bucket = None

        def log_exception():
            self.log(f"An exception got caught: {traceback.format_exc()}\n", LogLevel.ERROR)

        def execute_job():
            # Parse the job config and start the job console thread
            self.job_console.start(console_patterns=self.job_config.console_patterns)

            self.state = DUTState.RUNNING

            # Cut the power to the machine as early as possible, as we want to be
            # able to guarantee the power was off for the expected `min_off_time`,
            # and we can use some of that off time to setup the infra (download
            # kernel/initramfs, then push them to minio).
            self.pdu_port.set(PDUPortState.OFF)

            # Start the overall timeout
            timeouts = self.job_config.timeouts
            timeouts.overall.start()

            # Download all the artifacts (kernel/initramfs, container images, ...)
            self.log("Setup the infrastructure\n",
                     tag=ControlMessageTag.JOB_INFRA_SETUP_START)
            timeouts.infra_setup.start()
            if self.job_bucket:
                self.log("Initializing the job bucket with the client's data")
                self.job_bucket.setup()
            if self.cache_deployment(self.job_config.deployment, timeout=timeouts.infra_setup):
                self.log(f"Completed setup of the infrastructure, after {timeouts.infra_setup.active_for} s\n",
                         tag=ControlMessageTag.JOB_INFRA_SETUP_COMPLETE)
            else:
                timeout_active_for = timeouts.infra_setup.active_for
                self.log(f"Setting up the infrastructure timed out after {timeout_active_for} s. Aborting!\n",
                         tag=ControlMessageTag.JOB_INFRA_SETUP_ERROR)
                self.job_console.set_state(JobConsoleState.DUT_DONE)
            timeouts.infra_setup.stop()

            # Record the power usage at the start of the job so that we may compute
            # the energy consumed at the end of the job
            _, self.pdu_port_start_energy = self.get_pdu_port_power_energy()

            # Keep on resuming until success, timeouts' retry limits is hit, or the entire executor is going down
            self.cur_deployment = self.job_config.deployment_start
            while (not self.stop_event.is_set() and
                   not timeouts.overall.has_expired and
                   self.job_console.state < JobConsoleState.DUT_DONE):
                self.job_console.reset_per_boot_state()

                # Make sure the machine shuts down
                self.pdu_port.set(PDUPortState.OFF)
                self.firmware_boot_complete_event.clear()
                self.boot_pwr_samples = []
                boot_sequence_signaled = False

                # Reset the serial console ahead of starting the job so that it may recover from being in a bad state
                self.job_console.salad_console_reset()

                self.log(f"Power up the machine, enforcing {self.pdu_port.min_off_time} seconds of down time\n",
                         tag=ControlMessageTag.PDU_PORT_POWER_CYCLING_START)
                self.pdu_port.set(PDUPortState.ON)

                # Start the boot, and enable the timeouts!
                self.log("Boot the machine\n", tag=ControlMessageTag.PDU_PORT_POWER_CYCLING_COMPLETE)
                timeouts.boot_cycle.start()
                timeouts.first_console_activity.start()
                timeouts.firmware_boot.start()
                timeouts.console_activity.stop()

                # Reset all the watchdogs, since they are not supposed to remain active between rounds
                for wd in timeouts.watchdogs.values():
                    wd.stop()

                while (self.job_console.state < JobConsoleState.DUT_DONE and
                       not self.job_console.needs_reboot and
                       not self.stop_event.is_set() and
                       not timeouts.has_expired):

                    if timeouts.firmware_boot.is_started:
                        # Poll the power usage every second until the firmware boot event is signaled, after waiting
                        # 5 seconds so that we may safely ignore the in-rush power coming from charging the PSU's
                        # capacitors of the DUT, and instead focus on the standby/active power usage
                        if int(timeouts.firmware_boot.active_for.total_seconds()) - 5 > len(self.boot_pwr_samples):
                            port_pwr, _ = self.get_pdu_port_power_energy()

                            if port_pwr is not None:
                                self.boot_pwr_samples.append(port_pwr)

                                # Notify the user when the port power consumption exceeds the expected standby power
                                boot_sequence_pwr = (self.db_dut.boot_sequence_power or
                                                     int(config.DUT_DEFAULT_BOOT_SEQUENCE_POWER))
                                boot_seq_pwr_thrs = boot_sequence_pwr * BOOT_SEQUENCE_POWER_THRESHOLD_MULTIPLIER
                                if not boot_sequence_signaled and port_pwr >= boot_seq_pwr_thrs:
                                    # The power usage exceeds normal standby power, let's consider the DUT as having
                                    # initiated its boot power sequence.
                                    boot_sequence_signaled = True
                                    self.log(f"DUT power sequence detected: Power usage exceeds the maximum "
                                             f"expected standby power ({port_pwr:.1f}W >= {boot_seq_pwr_thrs:.1f}W)\n",
                                             tag=ControlMessageTag.DUT_POWER_SEQUENCE_DETECTED)

                        # Stop the firmware boot sequence timeout when the boot sequence event is signaled
                        if self.firmware_boot_complete_event.is_set():
                            self.firmware_boot_completed(timeouts.firmware_boot.active_for)
                            timeouts.firmware_boot.stop()
                            timeouts.firmware_boot.retried = 0

                    # Update the activity timeouts, based on when was the
                    # last time we sent it data
                    if self.job_console.last_activity_from_machine is not None:
                        timeouts.first_console_activity.stop()
                        timeouts.console_activity.reset(when=self.job_console.last_activity_from_machine)

                    # Wait a little bit before checking again
                    time.sleep(0.1)

                # Cut the power
                self.pdu_port.set(PDUPortState.OFF)

                # Increase the retry count of the timeouts that expired, and
                # abort the job if we exceeded their limits.
                abort = False
                for timeout in timeouts.expired_list:
                    retry = timeout.retry()
                    decision = "Try again!" if retry else "Abort!"
                    self.log(f"Hit the timeout {timeout} --> {decision}\n", LogLevel.ERROR,
                             tag=ControlMessageTag.TIMEOUT_HIT,
                             metadata={"timeout": {
                                        "name": timeout.name,
                                        "seconds": timeout.timeout.total_seconds(),
                                        "retries": timeout.retries,
                                        "retried": timeout.retried,
                                        "is_retrying": retry,
                                    }})
                    abort = abort or not retry

                    # If the DUT exceeded the firmware boot retries, queue a quick check to make sure it is in a
                    # working condition
                    if not retry and timeout == timeouts.firmware_boot and timeouts.firmware_boot.retried >= 2:
                        self.log(" -> Queuing a quick check on the DUT\n")
                        self.queue_quick_check()

                # Check if the DUT asked us to reboot
                if self.job_console.needs_reboot:
                    retry = timeouts.boot_cycle.retry()
                    retries_str = f"{timeouts.boot_cycle.retried}/{timeouts.boot_cycle.retries}"
                    dec = f"Boot cycle {retries_str}, go ahead!" if retry else "Exceeded boot loop count, aborting!"
                    self.log(f"The DUT asked us to reboot: {dec}\n", LogLevel.WARN)
                    abort = abort or not retry

                if abort:
                    # We have reached a timeout retry limit, time to stop!
                    self.job_console.set_state(JobConsoleState.DUT_DONE)
                else:
                    # Stop all the timeouts, except the overall
                    timeouts.first_console_activity.stop()
                    timeouts.firmware_boot.stop()
                    timeouts.console_activity.stop()
                    timeouts.boot_cycle.stop()

                    # We went through one boot cycle, use the "continue" deployment
                    self.cur_deployment = self.job_config.deployment_continue

            # We either reached the end of the job, or the client got disconnected
            if self.job_console.state == JobConsoleState.DUT_DONE:
                # Mark the machine as unfit for service
                if self.job_console.machine_is_unfit_for_service:
                    self.log("The machine has been marked as unfit for service\n")
                    self.update_mars_fields(ready_for_service=False)

                # Tearing down the job
                self.log("The job has finished executing, starting tearing down\n",
                         tag=ControlMessageTag.JOB_INFRA_TEARDOWN_START)
                timeouts.infra_teardown.start()

                # Delay to make sure messages are read before the end of the job
                time.sleep(CONSOLE_DRAINING_DELAY)

                # Calculate how much energy has been consumed
                if job_joules_consumed := self.joules_consumed:
                    job_wh_consumed = job_joules_consumed / 3600
                    self.log(f"The job consumed {job_wh_consumed:.3} Wh")

                # Start the tear down, which will create and send the credentials
                # for the job bucket to the client
                self.log("Creating credentials to the job bucket for the client\n")
                self.job_console.set_state(JobConsoleState.TEAR_DOWN, job_bucket=self.job_bucket,
                                           joules_consumed=job_joules_consumed)

                # Wait for the client to close the connection
                self.log("Waiting for the client to download the job bucket\n")
                while (self.job_console.state < JobConsoleState.OVER and
                       not self.stop_event.is_set() and
                       not timeouts.infra_teardown.has_expired):
                    # Wait a little bit before checking again
                    time.sleep(0.1)

                self.log(f"Completed the tear down procedure in {timeouts.infra_teardown.active_for} s\n",
                         tag=ControlMessageTag.JOB_INFRA_TEARDOWN_COMPLETE)
                timeouts.infra_teardown.stop()
            else:
                self.log("The job is over, skipping sharing the job bucket with the client")

            # We are done!

        try:
            # Ensure the job console is initialized
            if self.job_console is None:
                self.start_session()

            execute_job()
        except Exception:
            log_exception()
        finally:
            session_end()

    @property
    def job_status(self):
        if self.job_console is not None:
            return self.job_console.console_patterns.job_status
        else:
            return JobStatus.UNKNOWN

    def handle_tftp_request(self, request: TftpRequest):
        try:
            start = time.time()
            handler = JobTftpRequestHandler(executor=self, new_client=request)
            size = handler.artifact.filesize
            gen_time = time.time() - start

            self.log(f"{str(request)} - {size} bytes - {gen_time * 1000:.2f} ms")
        except Exception as e:
            self.log(f"{str(request)} - ignored - Reason: {str(e)}")
            raise e from None

    def handle_dhcp_request(self, request: DhcpRequest) -> DhcpDeployment:
        self.log(f"Received {request}")

        # Consider the firmware boot process complete
        self.firmware_boot_complete_event.set()

        # Only try matching the dhcp request to a device in our BootsDB
        # database if this was a netboot request since it would otherwise not
        # contain the information needed to identify the machine
        if request.is_valid_netboot_request:
            self.update_bootsdb_defaults_from_dhcp_request(request)

        # Return the matching DHCP entry
        if deployment := self.get_current_deployment():
            if deployment.dhcp:
                for entry in deployment.dhcp:
                    if entry.matches(request):
                        self.log(f"Using the DHCP config {entry}")
                        return entry

        self.log("No DHCP config found, using defaults")


app = flask.Flask(__name__)


def get_executor(raise_if_missing=True):
    with app.app_context():
        if executor := flask.current_app.executor:
            return executor
        elif raise_if_missing:
            raise ValueError("The executor has not started yet")


@app.errorhandler(Exception)
def handle_valueError_exception(error):
    traceback.print_exc()
    response = flask.jsonify({"error": str(error)})
    response.status_code = 400
    return response


@app.route('/api/v1/state', methods=['GET'])
def get_state():
    if executor := get_executor(raise_if_missing=False):
        return {
            "state": executor.state.name
        }
    else:
        return {
            "state": DUTState.QUEUED.name
        }


@app.route('/api/v1/boot/config', methods=['GET'])
def get_boot_config():
    args = flask.request.args

    executor = get_executor()
    if boot_cfg := executor.boot_config_query(platform=args.get("platform"),
                                              buildarch=args.get("buildarch"),
                                              bootloader=args.get("bootloader")):
        return asdict(boot_cfg)


@app.route('/api/v1/dhcp', methods=['PUT'])
def handle_dhcp_request():
    if request := flask.request.json.get("request"):
        dhcp_request = DhcpRequest(**yaml.safe_load(request))
        if dhcp_entry := get_executor().handle_dhcp_request(dhcp_request):
            return flask.make_response(dhcp_entry.options.serialize(), 200)
        else:
            return flask.make_response("No boot target found", 404)
    else:
        return flask.make_response("The request is missing", 400)


@app.route('/api/v1/fastboot', methods=['PUT'])
def handle_fastboot_device_added():
    get_executor().handle_fastboot_device_added()
    return ""


@app.route('/api/v1/tftp', methods=['PUT'])
def handle_tftp_request():
    yml_request = flask.request.json.get("request", "")
    request = TftpRequest(**yaml.safe_load(yml_request))

    try:
        get_executor().handle_tftp_request(request)
        return flask.make_response("The TFTP request was accepted\n", 200)
    except Exception as e:
        response = flask.jsonify({"error": str(e)})
        response.status_code = 404
        return response


@app.route('/api/v1/job/cancel', methods=['POST'])
def cancel_job():
    executor = get_executor()
    executor.cancel_job()
    return flask.make_response("The job was marked for cancellation\n", 200)


@dataclass
class JobConfig:
    executor_job_version: int

    mars_db: MarsDB
    machine_id: str

    job_request: JobRequest

    pdu_port_stats: PduPortStats

    @field_validator("executor_job_version")
    @classmethod
    def executor_job_version_is_known(cls, v):
        assert v == 1
        return v


def run(config_f, socket_path, lock_path):
    def parse_config(config_f):
        cfg = yaml.safe_load(config_f)
        return JobConfig(**cfg)

    try:
        # Create an exclusive lock
        print(f"# Acquiring the DUT's socket lock at {lock_path}", file=sys.stderr)
        os.makedirs(os.path.dirname(f"{socket_path}"), exist_ok=True)
        os.makedirs(os.path.dirname(f"{lock_path}"), exist_ok=True)
        socket_lock = open(lock_path, "w")
        lock_fd(socket_lock.fileno())
        socket_lock.write(f"{os.getpid()}\n")
        socket_lock.flush()

        # Parse the configuration
        print("# Parsing the job configuration", file=sys.stderr)
        cfg = parse_config(config_f)
        db_dut = cfg.mars_db.duts.get(cfg.machine_id)
        if db_dut is None:
            raise ValueError(f"The machine id '{cfg.machine_id}' can't be found in mars_db")

        # HACK: We should really find a way to get this set directly by pydantic!
        db_dut.id = cfg.machine_id

        # Create the executor
        print("# Instantiating the executor", file=sys.stderr)
        executor = Executor(mars_db=cfg.mars_db, db_dut=db_dut, job_request=cfg.job_request)

        # Update the configuration
        print("# Configuring Flask's context", file=sys.stderr)
        with app.app_context():
            flask.current_app.executor = executor
            flask.current_app.db_dut = db_dut

        # Disable Flask's access logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

        # Start Flask
        print("# Starting Flask", file=sys.stderr)
        flask_thread = threading.Thread(target=app.run, daemon=True,
                                        kwargs={"host": f"unix://{socket_path}",
                                                "port": None, "debug": True, "use_reloader": False})
        flask_thread.start()

        # Connect back to the client
        print("# Connect back to the client", file=sys.stderr)
        executor.start_session()

        # Instantiate the PDU port, and copy the port statistics from the server
        # so that we can avoid a long OFF->ON transition if the DUT has been OFF
        # for a while.
        print("# Instantiating the PDU port", file=sys.stderr)
        for f in fields(cfg.pdu_port_stats):
            setattr(executor.pdu_port, f.name, getattr(cfg.pdu_port_stats, f.name))

        # Start the job
        print("# Run the job", file=sys.stderr)
        executor.run()

        # Exit using the same status code as the job
        os._exit(executor.job_status.value)
    except Exception:
        # We caught an exception when we really shouldn't have, let's print it,
        # flush our streams, then die with the status code INCOMPLETE
        traceback.print_exc(file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(JobStatus.INCOMPLETE.value)
