from unittest.mock import MagicMock, patch, mock_open
from dataclasses import dataclass

from server.gitlab import (
    GitlabRunnerRegistration, register_runner, unregister_runner, runner_details,
    load_access_control_template, write_access_control_script, GitlabJobSource,
)
from server.gitlab import verify_runner_token, generate_gateway_runner_config, SanitizedFieldsMixin, Runner, RunnerType
from server.gitlab import generate_gateway_runner_tags
from server.mars import MarsDB, ConfigGitlabRunner, ConfigAcl, ConfigAclEntries
import server.config as config

from jinja2 import Template
import pytest


def test_SanitizedFieldsMixin__from_api():
    @dataclass
    class Dataclass(SanitizedFieldsMixin):
        field1: int
        field2: int

    assert Dataclass.from_api({"field1": 1, "field2": 2, "field3": 3}) == Dataclass(field1=1, field2=2)


def test_register_runner():
    url = "my url"
    registration_token = "reg_token"
    description = "toto"
    tag_list = ["tag1", "tag2"]

    runner_id = 1234
    runner_token = "my token"

    post_mock_return_value = MagicMock(status_code=201,
                                       json=MagicMock(return_value={"id": runner_id, "token": runner_token}))

    # Check the defaults
    with patch("server.gitlab.requests_session.post", return_value=post_mock_return_value) as post_mock:
        r = register_runner(gitlab_url=url, registration_token=registration_token,
                            description=description, tag_list=tag_list)
        assert r == GitlabRunnerRegistration(id=runner_id, token=runner_token)

        post_mock.assert_called_with(f"{url}/api/v4/user/runners",
                                     headers={"PRIVATE-TOKEN": registration_token},
                                     params={'description': description,
                                             'tag_list': ",".join(tag_list),
                                             'run_untagged': False,
                                             'maximum_timeout': 3600,
                                             'runner_type': 'instance_type'})

    # Check registration of a group runner
    with patch("server.gitlab.requests_session.post", return_value=post_mock_return_value) as post_mock:
        r = register_runner(gitlab_url=url, registration_token=registration_token,
                            description=description, tag_list=tag_list,
                            runner_type=RunnerType.GROUP, group_id=1234)
        assert r == GitlabRunnerRegistration(id=runner_id, token=runner_token)

        post_mock.assert_called_with(f"{url}/api/v4/user/runners",
                                     headers={"PRIVATE-TOKEN": registration_token},
                                     params={'description': description,
                                             'tag_list': ",".join(tag_list),
                                             'run_untagged': False,
                                             'maximum_timeout': 3600,
                                             'runner_type': 'group_type',
                                             'group_id': 1234})

    # Check registration of a project runner
    with patch("server.gitlab.requests_session.post", return_value=post_mock_return_value) as post_mock:
        r = register_runner(gitlab_url=url, registration_token=registration_token,
                            description=description, tag_list=tag_list,
                            runner_type=RunnerType.PROJECT, project_id=1234)
        assert r == GitlabRunnerRegistration(id=runner_id, token=runner_token)

        post_mock.assert_called_with(f"{url}/api/v4/user/runners",
                                     headers={"PRIVATE-TOKEN": registration_token},
                                     params={'description': description,
                                             'tag_list': ",".join(tag_list),
                                             'run_untagged': False,
                                             'maximum_timeout': 3600,
                                             'runner_type': 'project_type',
                                             'project_id': 1234})

    # Check that invalid types are rejected
    with pytest.raises(AssertionError):
        register_runner(gitlab_url=url, registration_token=registration_token,
                        description=description, tag_list=tag_list,
                        runner_type="invalid")

    # Check that we don't allow setting a runner type without the accompanying parameter
    for runner_type in [RunnerType.GROUP, RunnerType.PROJECT]:
        with pytest.raises(AssertionError):
            register_runner(gitlab_url=url, registration_token=registration_token,
                            description=description, tag_list=tag_list,
                            runner_type=runner_type)

    # Check that errors during registration return None
    with patch("server.gitlab.requests_session.post", return_value=MagicMock(status_code=403)) as post_mock:
        r = register_runner(gitlab_url=url, registration_token=registration_token,
                            description=description, tag_list=tag_list)
        assert r is None


def test_unregister_runner():
    url = "my url"
    runner_token = "my token"

    with patch("server.gitlab.requests_session.delete", return_value=MagicMock(status_code=204)) as delete_mock:
        assert unregister_runner(gitlab_url=url, token=runner_token)
        delete_mock.assert_called_with(f"{url}/api/v4/runners", params={"token": runner_token})

    with patch("server.gitlab.requests_session.delete", return_value=MagicMock(status_code=200)) as delete_mock:
        assert not unregister_runner(gitlab_url=url, token=runner_token)


def test_verify_runner_token():
    url = "my url"
    runner_token = "my token"

    with patch("server.gitlab.requests_session.post", return_value=MagicMock(status_code=200)) as post_mock:
        assert verify_runner_token(gitlab_url=url, token=runner_token)
        post_mock.assert_called_with(f"{url}/api/v4/runners/verify", params={"token": runner_token})

    with patch("server.gitlab.requests_session.post", return_value=MagicMock(status_code=403)) as post_mock:
        assert not verify_runner_token(gitlab_url=url, token=runner_token)


def test_runner_details():
    url = "my url"
    private_token = "my token"
    runner_id = 42

    details = {
        "id": runner_id,
        "description": "keywords-gfx10-1",
        "ip_address": "local_ip",
        "active": True,
        "paused": False,
        "is_shared": True,
        "runner_type": "instance_type",
        "name": None,
        "online": True,
        "status": "online",
        "tag_list": [
            "TAG1",
            "TAG2"
        ],
        "run_untagged": False,
        "locked": False,
        "maximum_timeout": 28800,
        "access_level": "not_protected",
        "version": "15.4.0",
        "revision": "43b2dc3d",
        "platform": "linux",
        "architecture": "amd64",
        "contacted_at": "2022-10-13T01:49:58.577Z",
        "projects": [],
        "groups": []}

    with patch("server.gitlab.requests_session.get",
               return_value=MagicMock(status_code=200,
                                      json=MagicMock(return_value=details))) as get_mock:
        runner = runner_details(gitlab_url=url, private_token=private_token, runner_id=runner_id)
        assert runner == Runner(id=runner_id, description="keywords-gfx10-1",
                                active=True, paused=False, online=True,
                                tag_list=["TAG1", "TAG2"], maximum_timeout=28800)
        get_mock.assert_called_with(f"{url}/api/v4/runners/{runner_id}",
                                    headers={"PRIVATE-TOKEN": private_token})

    with patch("server.gitlab.requests_session.get", return_value=MagicMock(status_code=401)) as get_mock:
        assert runner_details(gitlab_url=url, private_token=private_token, runner_id=runner_id) is None


def test_generate_gateway_runner_config():
    template_data = "data"

    with patch("server.gitlab.Template") as template_mock:
        with patch("builtins.open", mock_open(read_data=template_data)) as mock_file:
            with patch("server.gitlab.psutil") as psutil_mock:
                psutil_mock.cpu_count.return_value = 4
                psutil_mock.virtual_memory.return_value.total = 1e9

                mars_db = MagicMock()

                generate_gateway_runner_config(mars_db)

                template_mock.assert_called_with(template_data)
                template_mock.return_value.render.assert_called_with(config=config, mars_db=mars_db,
                                                                     cpu_count=4, ram_total_MB=1000)

                mock_file.return_value.write.assert_called_with(template_mock.return_value.render.return_value)


def test_gitlab_runner_config_template():
    pdus = {
        "apc": {
            "driver": "apc_drv",
            "config": {}
        }
    }

    duts = {
        "de:ad:be:ef:ca:fe": {
            "base_name": "gfx9",
            "tags": ["tag1", "tag2"],
            "mac_address": "de:ad:be:ef:ca:fe",
            "ip_address": "10.42.0.1",
            "local_tty_device": "ttyS0",
            "gitlab": {
                "freedesktop": {
                    "token": "mytoken",
                    "exposed": True
                }
            },
            "pdu": "apc",
            "pdu_port_id": 0,
            "pdu_off_delay": 30,
            "ready_for_service": True,
            "is_retired": False,
            "available": True,
        }
    }

    gitlab = {
        "freedesktop": {
            "url": "https://gitlab.freedesktop.org/",
            "registration_token": "<token>",
            "expose_runners": True,
            "maximum_timeout": 43200,
            "gateway_runner": {
                "token": "<token>",
                "exposed": True,
                "acl": {
                    "allow": {
                        "users": {
                            "foo.bar",
                        }
                    }
                }
            }
        }
    }

    mars_db = MarsDB(pdus=pdus, duts=duts, gitlab=gitlab)

    with open(config.GITLAB_CONF_TEMPLATE_FILE) as f:
        template = f.read()

    # Single board computers
    params = {
        "config": config,
        "mars_db": mars_db,
        "duts": duts,  # HACK: It should have been a DUT instance, but this is unnecessary for testing
        "cpu_count": 4,
        "ram_total_MB": 4096
    }
    config_toml = str(Template(template).render(**params))
    assert 'limit = 1' in config_toml
    assert 'cpus = 4  # Gateway runner CPU allocation'
    assert 'memory = "2048 MB" # Gateway runner memory allocation' in config_toml
    assert 'memory_swap = "2457 MB" # Gateway runner memory hard limit' in config_toml
    assert 'memory_reservation = "1024 MB" # Gateway runner memory soft limit' in config_toml

    # Recycled x86 computer
    params = {
        "config": config,
        "mars_db": mars_db,
        "duts": duts,
        "cpu_count": 8,
        "ram_total_MB": 16384
    }
    config_toml = str(Template(template).render(**params))
    assert 'limit = 1' in config_toml
    assert 'cpus = 8  # Gateway runner CPU allocation'
    assert 'memory = "12288 MB" # Gateway runner memory allocation' in config_toml
    assert 'memory_swap = "14745 MB" # Gateway runner memory hard limit' in config_toml
    assert 'memory_reservation = "6144 MB" # Gateway runner memory soft limit' in config_toml

    # Beefy server-class computer
    params = {
        "config": config,
        "mars_db": mars_db,
        "duts": duts,
        "cpu_count": 32,
        "ram_total_MB": 131072
    }
    config_toml = str(Template(template).render(**params))
    assert 'limit = 4' in config_toml
    assert 'cpus = 32  # Gateway runner CPU allocation'
    assert 'memory = "126976 MB" # Gateway runner memory allocation' in config_toml
    assert 'memory_swap = "152371 MB" # Gateway runner memory hard limit' in config_toml
    assert 'memory_reservation = "63488 MB" # Gateway runner memory soft limit' in config_toml

    assert mars_db.gitlab["freedesktop"].gateway_runner.acl.allow.tags(prefix="test") == {
        "test:acl:users:foo.bar",
    }


@patch('platform.machine', return_value="x86_64")
@patch('psutil.cpu_count', return_value=4)
@patch('psutil.virtual_memory', return_value=MagicMock(total=3544967296))
def test_generate_gateway_runner_tags__low_power(vm_mock, cpu_count_mock, platform_mock):
    config.FARM_NAME = 'helloworld'
    gateway_runner = ConfigGitlabRunner(
        acl=ConfigAcl(
            allow=ConfigAclEntries(
                users=[
                    'farm_admin',
                ]
            )
        )
    )
    assert generate_gateway_runner_tags(gateway_runner) == {
        'helloworld-gateway', 'CI-gateway', 'cpu:arch:x86_64',
        'cpu:cores:4', 'mem:size:4GiB',
        'ci-tron:gateway:acl:users:farm_admin',
    }


@patch('platform.machine', return_value="arm64")
@patch('psutil.cpu_count', return_value=32)
@patch('psutil.virtual_memory', return_value=MagicMock(total=28359738368))
def test_generate_gateway_runner_tags__beast_machine(vm_mock, cpu_count_mock, platform_mock):
    config.FARM_NAME = 'helloworld'
    gateway_runner = ConfigGitlabRunner(
        acl=ConfigAcl(
            allow=ConfigAclEntries(
                projects=[
                    'gfx-ci/ci-tron',
                ]
            )
        )
    )
    assert generate_gateway_runner_tags(gateway_runner) == {
        'helloworld-gateway', 'CI-gateway', 'cpu:arch:arm64',
        'cpu:cores:32', 'cpu:cores:8+', 'cpu:cores:16+', 'cpu:cores:32+',
        'mem:size:32GiB', 'mem:size:8+GiB', 'mem:size:32+GiB',
        'ci-tron:gateway:acl:projects:gfx-ci/ci-tron',
    }


def test_acl_script(tmpdir):
    acl_template = load_access_control_template()
    assert isinstance(acl_template, Template)

    with patch("server.gitlab.ACL_SCRIPT_FOLDER", tmpdir):
        write_access_control_script(template=acl_template, gl_name="fdo", dut_id=None, acls=[None])
        write_access_control_script(template=acl_template, gl_name="fdo", dut_id="de:ad:be:ef:ca:fe", acls=[])


def test_run_one_job(tmpdir):
    dut = MagicMock(id="de:ad:be:ef:ca:fe", full_name="farmname-dutname")
    dut_runner = MagicMock(token="gl-token")
    gl_instance = MagicMock(url="https://gitlab.example.local")
    # MagicMock().name is a special attribute that needs to be overridden after init
    gl_instance.name = "example"
    job_cookie = "JOB_COOKIE-test-value"

    run_single_command = [
        config.GITLAB_RUNNER_PATH,
        "run-single",
        "--max-builds", "1",
        "--wait-timeout", "1",
        "--limit", "1",
        "--name", "farmname-dutname",
        "--url", "https://gitlab.example.local",
        "--token", "gl-token",
        "--executor", "docker",
        "--docker-network-mode", "host",
        "--docker-shm-size", "0",
        "--docker-cpus", "1",
        "--docker-memory", "1GB",
        "--docker-memory-swap", "1GB",
        "--docker-memory-reservation", "512MB",
        "--docker-volumes", f"{str(tmpdir)}/instance-example-dut-de-ad-be-ef-ca-fe.sh:/access_control",
        "--pre-build-script", "/access_control",
        "--env", "CI_TRON_JOB_COOKIE=JOB_COOKIE-test-value",
        "--env", "MINIO_URL=http://ci-gateway:9000",
    ]

    job_src = GitlabJobSource(job_src=gl_instance, db_dut=dut, db_dut_job_src=dut_runner)
    job_src.job_cookie = job_cookie

    with patch("server.gitlab.ACL_SCRIPT_FOLDER", tmpdir):
        assert job_src._subprocess_kwargs() == {"args": run_single_command}
