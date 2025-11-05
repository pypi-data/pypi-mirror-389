# WARNING: Changes to this file need to be backwards/forwards compatible
# WARNING 2: You will need to keep the client's & server's message.py file in sync!

from dataclasses import dataclass, field
from functools import cached_property
from collections import namedtuple
from datetime import datetime, UTC
from enum import Enum, IntEnum

import struct
import base64
import json


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


class JobStatus(Enum):
    PASS = 0
    WARN = 1
    COMPLETE = 2
    FAIL = 3
    INCOMPLETE = 4
    UNKNOWN = 5
    SETUP_FAIL = 6

    @classmethod
    def from_str(cls, status):
        return getattr(cls, status, cls.UNKNOWN)

    @property
    def status_code(self):
        return self.value


class MessageType(Enum):
    CONTROL = "ctrl"  # A message meant to explain what is going on either ends
    JOB_IO = "job_io"
    SESSION_END = "session_end"

    @property
    def message_class(self):
        if self == self.CONTROL:
            return ControlMessage
        elif self == self.JOB_IO:
            return JobIOMessage
        elif self == self.SESSION_END:
            return SessionEndMessage


@dataclass
class Message:
    payload: str
    date: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def recv(cls, sock, length):
        buf = bytes()

        while len(buf) < length:
            received = sock.recv(length - len(buf))
            if len(received) == 0:
                raise EOFError("The connection got interrupted before receiving the end of the message")
            buf = buf + received

        return buf

    @classmethod
    def next_message(self, sock):
        length = struct.unpack("!I", self.recv(sock, 4))[0]
        frame = self.recv(sock, length)

        msg = json.loads(frame.decode())
        MessageTypeClass = MessageType(msg.get("msg_type")).message_class

        return MessageTypeClass(msg.get("payload"),
                                date=datetime.fromisoformat(msg.get('date')))

    def send(self, sock):
        payload = json.dumps({
            "msg_type": self.msg_type.value,
            "date": self.date.isoformat(),
            "payload": self.payload
        }).encode()

        return sock.send(struct.pack("!I", len(payload)) + payload)


# WARNING: NEVER CHANGE THE IDs OF EXISTING TAGS!
class ControlMessageTag(IntEnum):
    NO_TAG = 0

    JOB_INFRA_SETUP_START = 100
    JOB_INFRA_SETUP_COMPLETE = 101
    JOB_INFRA_SETUP_ERROR = 102
    JOB_INFRA_TEARDOWN_START = 105
    JOB_INFRA_TEARDOWN_COMPLETE = 106

    PDU_PORT_POWER_CYCLING_START = 200
    PDU_PORT_POWER_CYCLING_COMPLETE = 201

    DUT_POWER_SEQUENCE_DETECTED = 300
    DUT_FIRMWARE_BOOT_COMPLETE = 301

    TIMEOUT_HIT = 400

    DUT_CONSOLE_PATTERN_MATCHED = 401


class ControlMessage(Message):
    msg_type = MessageType.CONTROL

    @property
    def message(self) -> str:
        return self.payload.get("msg")

    @property
    def severity(self) -> LogLevel:
        return self.payload.get("severity")

    @property
    def tag(self) -> ControlMessageTag:
        try:
            return ControlMessageTag(self.payload.get("tag"))
        except ValueError:
            # Silently convert unknown tags to NO_TAG
            return ControlMessageTag.NO_TAG

    @property
    def metadata(self) -> dict:
        return self.payload.get("metadata", {})

    @classmethod
    def create(cls, message, severity=LogLevel.INFO,
               tag=ControlMessageTag.NO_TAG, metadata=dict()):
        return cls(payload={
            "msg": message,
            "severity": severity,
            "tag": tag,
            "metadata": metadata
        })


class JobIOMessage(Message):
    msg_type = MessageType.JOB_IO

    @property
    def buffer(self) -> bytes:
        return base64.b85decode(self.payload.encode())

    @classmethod
    def create(cls, buffer: bytes):
        return cls(payload=base64.b85encode(buffer).decode())


class SessionEndMessage(Message):
    msg_type = MessageType.SESSION_END

    @property
    def status(self):
        return JobStatus.from_str(self.payload.get("status"))

    @property
    def joules_consumed(self) -> float | None:
        return self.payload.get("joules_consumed")

    @cached_property
    def job_bucket(self):
        bucket = self.payload.get("job_bucket")
        if bucket is None:
            return None

        JobBucket = namedtuple("JobBucket", ["minio_access_url", "bucket_name"])
        return JobBucket(minio_access_url=bucket.get('minio_access_url'),
                         bucket_name=bucket.get('bucket_name'))

    @classmethod
    def create(cls, status, job_bucket=None, joules_consumed: float = None):
        parameters = {
            "status": status.name,
            "joules_consumed": joules_consumed,
        }

        if job_bucket:
            # TODO: Grant only read rights to the client
            job_bucket.create_owner_credentials("client")
            parameters['job_bucket'] = {
                "minio_access_url": job_bucket.access_url("client"),
                "bucket_name": job_bucket.name
            }

        return cls(payload=parameters)
