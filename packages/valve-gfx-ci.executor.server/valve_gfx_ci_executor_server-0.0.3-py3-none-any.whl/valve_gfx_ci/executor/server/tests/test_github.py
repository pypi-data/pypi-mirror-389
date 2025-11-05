from unittest.mock import MagicMock, patch
from pathlib import Path

from server.github import (
    GithubRunnerRegistration, Runner, GithubJobSource,
    _register_runner, _unregister_runner, _find_runner_by_name,
)
from server import config


def test_Runner_from_api():
    """Test Runner.from_api with label transformation"""
    runner_data = {
        "id": 123,
        "name": "test-runner",
        "os": "Linux",
        "status": "online",
        "busy": False,
        "labels": [
            {"id": 1, "name": "self-hosted"},
            {"id": 2, "name": "linux"},
            {"id": 3, "name": "x64"}
        ],
        "extra_field": "should_be_ignored"
    }

    runner = Runner.from_api(runner_data)

    assert runner.id == 123
    assert runner.name == "test-runner"
    assert runner.os == "Linux"
    assert runner.status == "online"
    assert runner.busy is False
    assert runner.labels == ["self-hosted", "linux", "x64"]


def test_register_runner_success():
    """Test successful runner registration"""
    url = "my url"
    authorization_token = "reg_token"
    name = "toto"
    labels = ["tag1", "tag2"]
    runner_id = 1234
    runner_group_id = 1

    post_mock_return_value = MagicMock(
        status_code=201,
        json=MagicMock(return_value={
            "runner": {
                "id": runner_id,
                "name": name,
                "os": "unknown",
                "status": "offline",
                "busy": False,
                "labels": labels,
                "runner_group_id": runner_group_id
            },
            "encoded_jit_config": "base64"
        })
    )

    with patch("server.github.requests_session.post", return_value=post_mock_return_value) as post_mock:
        r = _register_runner(
            github_url=url,
            authorization_token=authorization_token,
            name=name,
            labels=labels,
            runner_group_id=runner_group_id
        )

        assert r == GithubRunnerRegistration(id=runner_id, encoded_jit_config="base64")
        post_mock.assert_called_with(
            f"{url}/actions/runners/generate-jitconfig",
            headers={"Authorization": f"Bearer {authorization_token}"},
            json={
                'name': name,
                'labels': labels,
                'runner_group_id': runner_group_id,
                'work_folder': '_work'
            }
        )


def test_register_runner_failure():
    """Test failed runner registration returns None"""
    url = "my url"
    authorization_token = "reg_token"
    name = "toto"
    labels = ["tag1", "tag2"]

    with patch("server.github.requests_session.post", return_value=MagicMock(status_code=403)):
        r = _register_runner(
            github_url=url,
            authorization_token=authorization_token,
            name=name,
            labels=labels,
            runner_group_id=1
        )
        assert r is None


def test_register_runner_conflict():
    """Test runner registration handles 409 conflict"""
    url = "my url"
    authorization_token = "reg_token"
    name = "toto"
    labels = ["tag1", "tag2"]

    with patch("server.github.requests_session.post", return_value=MagicMock(status_code=409)):
        r = _register_runner(
            github_url=url,
            authorization_token=authorization_token,
            name=name,
            labels=labels,
            runner_group_id=1
        )
        assert r is None


def test_unregister_runner_success():
    """Test successful runner unregistration"""
    url = "my url"
    authorization_token = "my token"
    runner_id = 21

    with patch("server.github.requests_session.delete", return_value=MagicMock(status_code=204)) as delete_mock:
        result = _unregister_runner(
            github_url=url,
            authorization_token=authorization_token,
            runner_id=runner_id
        )

        assert result is True
        delete_mock.assert_called_with(
            f"{url}/actions/runners/{runner_id}",
            headers={"Authorization": f"Bearer {authorization_token}"}
        )


def test_unregister_runner_failure():
    """Test failed runner unregistration returns False"""
    url = "my url"
    authorization_token = "my token"
    runner_id = 21

    with patch("server.github.requests_session.delete", return_value=MagicMock(status_code=200)):
        result = _unregister_runner(
            github_url=url,
            authorization_token=authorization_token,
            runner_id=runner_id
        )
        assert result is False


def test_find_runner_by_name_success():
    """Test finding a runner by name"""
    url = "https://api.github.com"
    token = "test-token"
    name = "test-runner"

    runner_data = {
        "runners": [
            {
                "id": 123,
                "name": "other-runner",
                "os": "Linux",
                "status": "online",
                "busy": False,
                "labels": [{"name": "tag1"}]
            },
            {
                "id": 456,
                "name": "test-runner",
                "os": "Linux",
                "status": "online",
                "busy": True,
                "labels": [{"name": "tag2"}]
            }
        ]
    }

    with patch("server.github.requests_session.get",
               return_value=MagicMock(status_code=200, json=MagicMock(return_value=runner_data))):
        runner = _find_runner_by_name(url, token, name)

        assert runner is not None
        assert runner.id == 456
        assert runner.name == "test-runner"
        assert runner.busy is True


def test_find_runner_by_name_not_found():
    """Test finding a runner that doesn't exist"""
    url = "https://api.github.com"
    token = "test-token"
    name = "nonexistent-runner"

    runner_data = {"runners": []}

    with patch("server.github.requests_session.get",
               return_value=MagicMock(status_code=200, json=MagicMock(return_value=runner_data))):
        runner = _find_runner_by_name(url, token, name)
        assert runner is None


def test_find_runner_by_name_api_failure():
    """Test handling API failure when finding runner"""
    url = "https://api.github.com"
    token = "test-token"
    name = "test-runner"

    with patch("server.github.requests_session.get", return_value=MagicMock(status_code=500)):
        runner = _find_runner_by_name(url, token, name)
        assert runner is None


def test_is_runner_online_true():
    """Test checking if a runner is online"""
    url = "https://api.github.com"
    token = "test-token"
    runner_id = 123

    runner_data = {
        "id": 123,
        "name": "test-runner",
        "os": "Linux",
        "status": "online",
        "busy": False,
        "labels": [{"name": "tag1"}]
    }

    with patch("server.github.requests_session.get",
               return_value=MagicMock(status_code=200, json=MagicMock(return_value=runner_data))):
        from server.github import _is_runner_online
        result = _is_runner_online(url, token, runner_id)
        assert result is True


def test_is_runner_online_false_offline_status():
    """Test checking if a runner is offline"""
    url = "https://api.github.com"
    token = "test-token"
    runner_id = 123

    runner_data = {
        "id": 123,
        "name": "test-runner",
        "os": "Linux",
        "status": "offline",
        "busy": False,
        "labels": [{"name": "tag1"}]
    }

    with patch("server.github.requests_session.get",
               return_value=MagicMock(status_code=200, json=MagicMock(return_value=runner_data))):
        from server.github import _is_runner_online
        result = _is_runner_online(url, token, runner_id)
        assert result is False


def test_is_runner_online_false_api_failure():
    """Test checking runner online status when API fails"""
    url = "https://api.github.com"
    token = "test-token"
    runner_id = 123

    with patch("server.github.requests_session.get", return_value=MagicMock(status_code=404)):
        from server.github import _is_runner_online
        result = _is_runner_online(url, token, runner_id)
        assert result is False


def test_GithubJobSource_setup_job_success():
    """Test successful job setup"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token", runner_group_id=None),
        db_dut=MagicMock(),
        db_dut_job_src=MagicMock(description="test-dut", tags=["tag1", "tag2"], runner_group_id=42)
    )

    mock_runner_dir = MagicMock()
    mock_runner_dir.exists.return_value = True
    mock_run_sh = MagicMock()
    mock_run_sh.exists.return_value = True
    mock_runner_dir.__truediv__.return_value = mock_run_sh

    mock_registration = GithubRunnerRegistration(id=123, encoded_jit_config="jit_config")

    with patch("server.github._find_runner_by_name", return_value=None), \
         patch("server.github._register_runner", return_value=mock_registration) as mock_register:

        result = job_src._setup_job()

        assert result is True
        assert job_src.runner_id == 123
        assert job_src.encoded_jit_config == "jit_config"
        assert job_src.runner_group_id == 42
        mock_register.assert_called_once_with(
            github_url="https://api.github.com",
            authorization_token="token",
            name="test-dut",
            labels=["tag1", "tag2"],
            runner_group_id=42
        )


def test_GithubJobSource_setup_job_uses_fallback_runner_group_id():
    """Test job setup falls back to runner_group_id=1"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token", runner_group_id=None),
        db_dut=MagicMock(full_name="test-dut", all_tags=["tag1"]),
        db_dut_job_src=MagicMock(runner_group_id=None)
    )

    mock_runner_dir = MagicMock()
    mock_runner_dir.exists.return_value = True
    mock_run_sh = MagicMock()
    mock_run_sh.exists.return_value = True
    mock_runner_dir.__truediv__.return_value = mock_run_sh

    mock_registration = GithubRunnerRegistration(id=123, encoded_jit_config="jit_config")

    with patch("server.github._find_runner_by_name", return_value=None), \
         patch("server.github._register_runner", return_value=mock_registration) as mock_register:

        result = job_src._setup_job()

        assert result is True
        assert job_src.runner_group_id == 1
        call_kwargs = mock_register.call_args[1]
        assert call_kwargs['runner_group_id'] == 1


def test_GithubJobSource_setup_job_cleans_up_stale_runner():
    """Test job setup unregisters stale runner"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token"),
        db_dut=MagicMock(full_name="test-dut", all_tags=[]),
        db_dut_job_src=MagicMock(runner_group_id=1)
    )

    mock_runner_dir = MagicMock()
    mock_runner_dir.exists.return_value = True
    mock_run_sh = MagicMock()
    mock_run_sh.exists.return_value = True
    mock_runner_dir.__truediv__.return_value = mock_run_sh

    stale_runner = Runner(id=999, name="test-dut", os="Linux", status="offline", busy=False, labels=[])
    mock_registration = GithubRunnerRegistration(id=123, encoded_jit_config="jit_config")

    with patch("server.github._find_runner_by_name", return_value=stale_runner), \
         patch("server.github._unregister_runner") as mock_unregister, \
         patch("server.github._register_runner", return_value=mock_registration):

        result = job_src._setup_job()

        assert result is True
        mock_unregister.assert_called_once_with(
            github_url="https://api.github.com",
            authorization_token="token",
            runner_id=999
        )


def test_GithubJobSource_setup_job_registration_fails():
    """Test job setup fails when runner registration fails"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token"),
        db_dut=MagicMock(full_name="test-dut", all_tags=[]),
        db_dut_job_src=MagicMock(runner_group_id=1)
    )

    mock_runner_dir = MagicMock()
    mock_runner_dir.exists.return_value = True
    mock_run_sh = MagicMock()
    mock_run_sh.exists.return_value = True
    mock_runner_dir.__truediv__.return_value = mock_run_sh

    with patch("server.github._find_runner_by_name", return_value=None), \
         patch("server.github._register_runner", return_value=None):  # Registration fails

        result = job_src._setup_job()
        assert result is False


def test_GithubJobSource_try_cancel_job_pickup_success():
    """Test successful job pickup cancellation"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token"),
        db_dut=MagicMock(),
        db_dut_job_src=MagicMock()
    )
    job_src.runner_id = 123

    with patch("server.github._unregister_runner", return_value=True):
        result = job_src._try_cancel_job_pickup()
        assert result is True


def test_GithubJobSource_try_cancel_job_pickup_fails():
    """Test failed job pickup cancellation (job already picked up)"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token"),
        db_dut=MagicMock(),
        db_dut_job_src=MagicMock()
    )
    job_src.runner_id = 123

    with patch("server.github._unregister_runner", return_value=False):
        result = job_src._try_cancel_job_pickup()
        assert result is False


def test_GithubJobSource_runner_job_polling_complete_true():
    """Test runner job polling complete returns true when online"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token"),
        db_dut=MagicMock(),
        db_dut_job_src=MagicMock()
    )
    job_src.runner_id = 123

    with patch("server.github._is_runner_online", return_value=True):
        result = job_src._runner_job_polling_complete()
        assert result is True


def test_GithubJobSource_runner_job_polling_complete_false():
    """Test runner job polling complete returns false when offline"""
    job_src = GithubJobSource(
        job_src=MagicMock(url="https://api.github.com", authorization_token="token"),
        db_dut=MagicMock(),
        db_dut_job_src=MagicMock()
    )
    job_src.runner_id = 123

    with patch("server.github._is_runner_online", return_value=False):
        result = job_src._runner_job_polling_complete()
        assert result is False


def test_GithubJobSource_subprocess_kwargs():
    """Test subprocess kwargs generation"""
    job_src = GithubJobSource(
        job_src=MagicMock(),
        db_dut=MagicMock(),
        db_dut_job_src=MagicMock()
    )
    job_src.runner_dir = Path("/test/runner")
    job_src.encoded_jit_config = "test_jit_config"
    job_src.job_cookie = "test_cookie"

    kwargs = job_src._subprocess_kwargs()

    assert kwargs['env']['CI_TRON_JOB_COOKIE'] == "test_cookie"
    assert kwargs['env']['PATH'] == "/usr/bin:/usr/local/bin"
    assert kwargs['args'] == [config.GITHUB_RUNNER_PATH, "--jitconfig", "test_jit_config"]
