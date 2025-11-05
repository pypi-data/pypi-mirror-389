import pytest
import signal

from unittest.mock import patch, MagicMock, call
from pathlib import Path

from server.nbd import create_tmp_raw_backing, Nbd

import server.config as config


def test_create_tmp_raw_backing():
    path = Path(create_tmp_raw_backing(1234))

    assert path.exists()
    assert path.stat().st_size == 1234
    assert path.stat().st_blocks == 0

    link_path = str(path.readlink())
    assert link_path.startswith(str(config.EXECUTOR_NBD_ROOT))
    assert link_path.endswith("(deleted)")


def test_Nbd_qemu_nbd_args():
    nbd = Nbd(name="name", backing="/backing", backing_read_only=True, export_as_read_only=False, max_connections=10)

    assert nbd._qemu_nbd_args(tcp_port=8080, pid_file="/pid") == [
        "qemu-nbd", "-f", "raw", "-p", "8080", "--fork", "--pid-file", "/pid", "--shared", "10", '--persistent',
        "-s", "/backing"
    ]

    nbd = Nbd(name="name", backing="/backing", backing_read_only=False)
    assert nbd._qemu_nbd_args(tcp_port=8080, pid_file="/pid") == [
        "qemu-nbd", "-f", "raw", "-p", "8080", "--fork", "--pid-file", "/pid", "--shared", "4", '--persistent',
        "/backing"
    ]


def mock_qemu_nbd_args(tcp_port, pid_file):
    assert tcp_port > 1024
    assert tcp_port <= 65535
    Path(pid_file).write_text("1\n")

    return ["qemu-nbd", "args"]


@patch("server.nbd.run")
def test_Nbd_setup__success(run_mock):
    nbd = Nbd(name="name", backing="/backing", backing_read_only=True)

    run_mock.return_value = MagicMock(returncode=0)
    nbd._qemu_nbd_args = mock_qemu_nbd_args

    run_mock.assert_not_called()
    nbd.setup(timeout=4)
    run_mock.assert_called_with(["qemu-nbd", "args"], stdout=-1, stderr=-2, timeout=4)

    assert nbd.hostname == "ci-gateway"
    assert nbd.tcp_port == nbd._cached_setup[0]
    assert nbd.server_pidfd == nbd._cached_setup[1]
    assert nbd.to_b2c_nbd("/dev/nbd0") == (f"b2c.nbd=/dev/nbd0,host={nbd.hostname},port={nbd.tcp_port},"
                                           f"connections={nbd.max_connections}")


@patch("server.nbd.run")
def test_Nbd_setup__fail(run_mock):
    nbd = Nbd(name="name", backing="/backing", backing_read_only=True)

    run_mock.return_value = MagicMock(returncode=1, stdout="My error log")
    nbd._qemu_nbd_args = MagicMock()

    run_mock.assert_not_called()
    with pytest.raises(ValueError) as exc:
        nbd.setup()
    assert "Exit code 1, Output:\nMy error log" in str(exc.value)

    # Make sure we tried multiple times, every time with a different tcp port
    assert run_mock.call_count == 10
    assert nbd._qemu_nbd_args.call_count == 10
    tcp_ports = list()
    for kall in nbd._qemu_nbd_args.call_args_list:
        assert kall[0][1] == nbd._qemu_nbd_args.call_args_list[0][0][1]
        tcp_ports.append(kall[0][0])
    assert len(tcp_ports) == len(set(tcp_ports))


@patch("server.nbd.signal.pidfd_send_signal")
@patch("server.nbd.select.select", return_value=([], [], []))
def test_Nbd_teardown(select_mock, pidfd_send_mock):
    nbd = Nbd(name="name", backing="/backing", backing_read_only=True)

    nbd._cached_setup = (8080, 42)
    nbd.teardown()

    assert pidfd_send_mock.call_args_list == [
        call(42, signal.SIGTERM),
        call(42, signal.SIGKILL)
    ]
    select_mock.assert_called_once_with([42], [], [], 1)
