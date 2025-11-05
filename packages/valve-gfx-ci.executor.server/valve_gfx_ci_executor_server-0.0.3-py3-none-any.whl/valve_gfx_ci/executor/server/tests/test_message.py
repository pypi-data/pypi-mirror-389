from unittest.mock import MagicMock
from datetime import datetime
import logging
import base64

from server.message import Message, MessageType, ControlMessage, JobIOMessage, SessionEndMessage, JobStatus
from server.message import LogLevel, ControlMessageTag
import pytest


def test_JobStatus():
    for status in JobStatus:
        assert status.status_code == status.value
        assert JobStatus.from_str(status.name) == status


def test_MessageType_message_class():
    assert MessageType.CONTROL.message_class == ControlMessage
    assert MessageType.JOB_IO.message_class == JobIOMessage
    assert MessageType.SESSION_END.message_class == SessionEndMessage


def test_ControlMessage__defaults():
    msg = ControlMessage.create('')

    assert msg.message == ''
    assert msg.severity == LogLevel.INFO
    assert msg.tag == ControlMessageTag.NO_TAG
    assert msg.metadata == {}


def test_ControlMessage():
    message = "Hello world"
    severity = logging.CRITICAL
    tag = ControlMessageTag.JOB_INFRA_SETUP_START
    metadata = {"hello": "world"}
    msg = ControlMessage.create(message=message, severity=severity, tag=tag, metadata=metadata)
    assert msg.message == message
    assert msg.severity == severity
    assert msg.tag == tag
    assert msg.metadata == metadata


def test_ControlMessage__unknown_tag_gets_converted_to_unknown():
    msg = ControlMessage.create(message='', tag=4242)
    assert msg.tag == ControlMessageTag.NO_TAG


def test_JobIOMessage():
    payload = b'Hello world'
    msg = JobIOMessage.create(b'Hello world')
    assert msg.payload == base64.b85encode(payload).decode()
    assert msg.buffer == payload


def test_SessionEndMessage():
    joules_consumed = 42

    parameters = {
        "status": JobStatus.PASS.name,
        'joules_consumed': joules_consumed,
    }
    msg = SessionEndMessage.create(status=JobStatus.PASS, joules_consumed=joules_consumed)
    assert msg.payload == parameters
    assert msg.status == JobStatus.PASS
    assert msg.joules_consumed == joules_consumed
    assert msg.job_bucket is None

    # Test the bucket
    bucket = MagicMock()
    bucket.name = "bucketname"
    bucket.access_url.return_value = "http://myurl"

    msg = SessionEndMessage.create(status=JobStatus.PASS,
                                   job_bucket=bucket)
    assert msg.job_bucket.minio_access_url == "http://myurl"
    assert msg.job_bucket.bucket_name == "bucketname"
    bucket.access_url.create_owner_credentials("client")
    bucket.access_url.assert_called_with("client")


def test_Message_send_receive():
    end_session_msg = {
        "status": JobStatus.PASS.name
    }
    expected_header = b'\x00\x00\x00\x59'
    expected_payload = b'{"msg_type": "session_end", "date": "1970-01-01T00:00:00", "payload": {"status": "PASS"}}'

    # Test the sending of messages
    sock_mock = MagicMock()
    send_msg = SessionEndMessage(date=datetime(year=1970, month=1, day=1), payload=end_session_msg)
    assert send_msg.send(sock_mock) == sock_mock.send.return_value
    sock_mock.send.assert_called_with(expected_header + expected_payload)

    # Test the reception of messages
    def side_effect(length):
        if length == len(expected_header):
            data = expected_header
        elif length == len(expected_payload):
            data = expected_payload
        else:
            raise ValueError("Unexpected length")  # pragma: no cover

        return data

    sock_mock = MagicMock(recv=MagicMock(side_effect=side_effect))
    recv_msg = Message.next_message(sock_mock)
    assert recv_msg == send_msg


def test_Message_recv_helper():
    def side_effect(length):
        if length == 10:
            return b'012345'
        elif length == 4:
            return b'6789'
        else:
            raise ValueError("Unexpected length")  # pragma: no cover

    sock_mock = MagicMock(recv=MagicMock(side_effect=side_effect))
    assert Message.recv(sock_mock, 10) == b'0123456789'

    sock_mock = MagicMock(recv=MagicMock(side_effect=[b'']))
    with pytest.raises(EOFError) as exc:
        Message.recv(sock_mock, 42)
    assert "The connection got interrupted before receiving the end of the message" in str(exc.value)
