from unittest.mock import patch

import socket
import os

from server.socketactivation import (
    named_fds,
    get_sockets_by_name
)


def test_named_fds():
    # Make sure no FDs are found when LISTEN_PID is unset
    assert named_fds() == {}

    # Make sure no FDs are found when LISTEN_PID is wrong
    os.environ["LISTEN_PID"] = str(os.getpid() + 1)
    assert named_fds() == {}

    # Valid LISTEN_PID, but LISTEN_FDS is missing
    os.environ["LISTEN_PID"] = str(os.getpid())
    assert named_fds() == {}

    # Invalid LISTEN_FDS
    os.environ["LISTEN_FDS"] = "invalid"
    assert named_fds() == {}

    # Valid LISTEN_FDS, but no names
    os.environ["LISTEN_FDS"] = "4"
    assert named_fds() == {None: [3, 4, 5, 6]}

    # With some names missing
    os.environ["LISTEN_FDNAMES"] = "name1:name2:name1"
    assert named_fds() == {"name1": [3, 5], "name2": [4], None: [6]}

    # With too many names (last names ignored)
    os.environ["LISTEN_FDNAMES"] = "name1:name2:name1:name3:name4"
    assert named_fds() == {"name1": [3, 5], "name2": [4], "name3": [6]}


@patch("server.socketactivation.named_fds")
def test_get_sockets_by_name(named_fds):
    with (socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1,
          socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, 0) as s2,
          socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s3):

        named_fds.return_value = {"http": [s1.fileno(), s3.fileno()], None: [s2.fileno()]}

        # Check the default socket parameters
        http_sockets = get_sockets_by_name("http")
        assert len(http_sockets) == 2
        for s in http_sockets:
            assert s.family == socket.AF_INET
            assert s.type == socket.SOCK_STREAM
            assert s.proto == 0

        # Check no name, but specified
        noname_sockets = get_sockets_by_name(family=socket.AF_INET6, type=socket.SOCK_DGRAM, proto=0)
        assert len(noname_sockets) == 1
        for s in noname_sockets:
            assert s.family == socket.AF_INET6
            assert s.type == socket.SOCK_DGRAM
            assert s.proto == 0
