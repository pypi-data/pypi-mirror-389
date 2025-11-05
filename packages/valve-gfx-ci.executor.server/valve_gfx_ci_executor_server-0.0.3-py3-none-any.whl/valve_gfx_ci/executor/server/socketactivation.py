import socket
import os

from collections import defaultdict


def named_fds():
    # Ignore any FDs that were not meant for us
    if os.environ.get('LISTEN_PID', None) != str(os.getpid()):
        return {}

    try:
        listen_fds_nr = int(os.getenv("LISTEN_FDS"))
    except Exception:
        return {}

    FIRST_SOCKET_FD = 3
    fds = [FIRST_SOCKET_FD + i for i in range(listen_fds_nr)]
    names = os.getenv("LISTEN_FDNAMES", "").split(":")

    named_fds = defaultdict(list)
    for i, fd in enumerate(fds):
        name = names[i] if i < len(names) and names[i] else None
        named_fds[name].append(fd)

    return named_fds


def get_sockets_by_name(name=None, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
    fds = named_fds().get(name, [])
    return [socket.socket(family, type, proto, fd) for fd in fds]
