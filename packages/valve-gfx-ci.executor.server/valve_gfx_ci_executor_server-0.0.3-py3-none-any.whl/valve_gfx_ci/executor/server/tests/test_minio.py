from unittest.mock import call, patch, MagicMock
from urllib.parse import urlparse
import subprocess
import tarfile
import json

from minio.error import S3Error
import pytest

from server.minioclient import MinioClient, MinIOPolicyStatement, generate_policy
import server.config as config


def test_generate_policy():
    statement1 = MinIOPolicyStatement()
    statement2 = MinIOPolicyStatement(buckets=['bucket1', 'bucket2'],
                                      actions=["action1", "action2"],
                                      source_ips=["ip1", "ip2"])
    statement3 = MinIOPolicyStatement(buckets=['bucket2'],
                                      actions=["action1", "action3"],
                                      allow=False, not_source_ips=["ip3"])

    assert generate_policy([statement1, statement2, statement3]) == {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["s3:*"],
                "Effect": "Allow",
                "Resource": ['arn:aws:s3:::*', 'arn:aws:s3:::*/*'],
            },
            {
                "Action": ["action1", "action2"],
                "Effect": "Allow",
                "Resource": ['arn:aws:s3:::bucket1', 'arn:aws:s3:::bucket2',
                             'arn:aws:s3:::bucket1/*', 'arn:aws:s3:::bucket2/*'],
                "Condition": {
                    "IpAddress": {
                        "aws:SourceIp": ["ip1", "ip2"]
                    }
                }
            },
            {
                "Action": ["action1", "action3"],
                "Effect": "Deny",
                "Resource": ['arn:aws:s3:::bucket2', 'arn:aws:s3:::bucket2/*'],
                "Condition": {
                    "NotIpAddress": {
                        "aws:SourceIp": ["ip3"]
                    }
                }
            }
        ]
    }


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
def test_client_instantiation__defaults(subproc_mock, minio_mock):
    MinioClient()
    minio_mock.assert_called_once_with(endpoint=urlparse(config.MINIO_URL).netloc,
                                       access_key=config.MINIO_ROOT_USER, secret_key=config.MINIO_ROOT_PASSWORD,
                                       secure=False)
    subproc_mock.assert_called_once_with(['mcli', '--no-color', 'alias', 'set',
                                          config.MINIO_ADMIN_ALIAS, config.MINIO_URL,
                                          config.MINIO_ROOT_USER, config.MINIO_ROOT_PASSWORD])


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
def test_client_instantiation__custom_params(subproc_mock, minio_mock):
    MinioClient(url="http://hello-world", user="accesskey", secret_key="secret_key", alias="toto")
    minio_mock.assert_called_once_with(endpoint="hello-world", access_key="accesskey",
                                       secret_key="secret_key", secure=False)
    subproc_mock.assert_called_once_with(['mcli', '--no-color', 'alias', 'set',
                                          "toto", "http://hello-world", "accesskey", "secret_key"])


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
def test_client_instantiation__no_aliases(subproc_mock, minio_mock):
    MinioClient(url="http://hello-world", user="accesskey", secret_key="secret_key", alias=None)
    minio_mock.assert_called_once_with(endpoint="hello-world", access_key="accesskey",
                                       secret_key="secret_key", secure=False)
    subproc_mock.assert_not_called()


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output")
def test_client_remove_alias(check_output_mock, subproc_mock, minio_mock):
    client = MinioClient(url="http://hello-world", user="accesskey", secret_key="secret_key", alias="toto")
    subproc_mock.assert_called_once_with(['mcli', '--no-color', 'alias', 'set',
                                          "toto", "http://hello-world", "accesskey", "secret_key"])

    client.remove_alias()
    check_output_mock.assert_called_with(['mcli', '--no-color', 'alias', 'rm', "toto"])


@patch("server.minioclient.Minio", autospec=True)
@patch("server.minioclient.TarFile.open", autospec=True)
@patch("subprocess.check_call")
def test_extract_archive(subproc_mock, tarfile_mock, minio_mock):
    client = MinioClient()

    archive_mock = tarfile_mock.return_value.__enter__.return_value
    file_obj = MagicMock()

    member1 = MagicMock(spec=tarfile.TarInfo)
    member1.isfile = MagicMock(return_value=True)
    member1.size.return_value = 42
    member1.mode = 0o777
    member1.get_info.return_value = {
        'gid': 1,
        'gname': 'group',
        'mtime': 42,
        'uid': 2,
        'uname': 'frank'
    }

    members = [member1, MagicMock(isfile=MagicMock(return_value=False)), None]
    members[0].name = "toto"
    archive_mock.next = MagicMock(side_effect=members)

    client.extract_archive(file_obj, "bucket/rootpath")

    tarfile_mock.assert_called_once_with(fileobj=file_obj, mode='r')
    archive_mock.extractfile.assert_called_once_with(members[0])

    client._client.put_object.assert_called_once_with(
        "bucket/rootpath",
        "toto",
        archive_mock.extractfile(),
        members[0].size,
        num_parallel_uploads=1,
        metadata={'X-Amz-Meta-Mc-Attrs': 'gid:1/gname:group/mode:2384495103/mtime:42/uid:2/uname:frank'})


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
def test_make_bucket(subproc_mock, minio_mock):
    client = MinioClient()
    client._client = MagicMock()
    client.make_bucket('test-id')
    client._client.make_bucket.assert_called_once_with('test-id')

    def side_effect(*arg, **kwargs):
        raise S3Error('code', 'message', 'resource', 'request_id', 'host_id', 'response')
    client._client.make_bucket.side_effect = side_effect

    with pytest.raises(ValueError) as exc:
        client.make_bucket('test-id')
    assert "The bucket already exists" in str(exc.value)


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
def test_bucket_exists(subproc_mock, minio_mock):
    client = MinioClient()
    client._client = MagicMock()
    ret = client.bucket_exists('test-id')
    client._client.bucket_exists.assert_called_once_with('test-id')

    assert ret == client._client.bucket_exists.return_value


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output")
def test_remove_bucket(check_output_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.remove_bucket('test-id')
    check_output_mock.assert_called_with(['mcli', '--no-color', 'rb', '--force', 'local/test-id'])


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output")
def test_minio_add_user(check_output_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.add_user('job-id-c', 'job-password')
    check_output_mock.assert_called_with(['mcli', '--no-color', 'admin', 'user', 'add', 'local',
                                          'job-id-c', 'job-password'])


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output")
def test_minio_remove_user(check_output_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.remove_user('username')
    check_output_mock.assert_called_with(['mcli', '--no-color', 'admin', 'user', 'remove', 'local', 'username'])


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output", return_value="""{"status": "success", "accessKey": "username",
    "userStatus": "enabled", "memberOf": ["group1", "group2"]}""")
def test_minio_groups_user_is_in(subproc_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    assert client.groups_user_is_in() == {"group1", "group2"}
    assert client.groups_user_is_in('username') == {"group1", "group2"}
    subproc_mock.assert_has_calls([
        call(['mcli', '--no-color', '--json', 'admin', 'user', 'info', 'local', 'test']),
        call(['mcli', '--no-color', '--json', 'admin', 'user', 'info', 'local', 'username'])
    ])


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output", return_value="""{"status": "success", "accessKey": "username",
    "userStatus": "enabled", "memberOf": [{"name": "group1"}, {"name": "group2"}]}""")
def test_minio_groups_user_is_in__newformat(subproc_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    assert client.groups_user_is_in() == {"group1", "group2"}


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output",
       side_effect=subprocess.CalledProcessError(1, ["cmd", "arg"], output="An error message"))
def test_minio_groups_user_is_in__callprocess_error(subproc_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    with pytest.raises(ValueError) as e:
        client.groups_user_is_in()
    assert "Failed to query information about the user" in str(e)


@patch("server.minioclient.Minio", autospec=True)
@patch("subprocess.check_call")
@patch("subprocess.check_output")
def test_minio_add_user_to_group(check_output_mock, _, minio_mock):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.add_user_to_group('username', 'groupname')
    check_output_mock.assert_called_with(['mcli', '--no-color', 'admin', 'group', 'add', 'local',
                                          'groupname', 'username'])


@patch("subprocess.check_call")
@patch("server.minioclient.tempfile.NamedTemporaryFile", autospec=True)
@patch("subprocess.check_output")
def test_minio_apply_user_policy(check_output_mock, named_temp_mock, _):
    temp_mock = MagicMock()
    temp_mock.name = '/tmp/temp_file'
    named_temp_mock.return_value.__enter__.return_value = temp_mock

    policy_statements = [MinIOPolicyStatement(['bucket'])]
    expected_policy = generate_policy(policy_statements)

    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.apply_user_policy('policy_name', 'username', policy_statements=policy_statements)

    temp_mock.write.assert_called_once_with(json.dumps(expected_policy).encode())

    check_output_mock.assert_has_calls([
        call(['mcli', '--no-color', 'admin', 'policy', 'create', 'local', 'policy_name', '/tmp/temp_file']),
        call(['mcli', '--no-color', '--json', 'admin', 'policy', 'attach', 'local', 'policy_name',
              '--user', 'username'])])


def mcli_mock(cmd, error_code):
    if 'attach' in cmd:
        output = {
            "error": {
                "cause": {
                    "error": {
                        "Code": error_code
                    }
                }
            }
        }
        raise subprocess.CalledProcessError(returncode=1, cmd=[], output=json.dumps(output))


@patch("subprocess.check_call")
@patch("server.minioclient.tempfile.NamedTemporaryFile", autospec=True)
@patch("subprocess.check_output", side_effect=lambda cmd: mcli_mock(cmd, "XMinioPolicyAlreadyAttached"))
def test_minio_apply_user_policy__already_attached(check_output_mock, __, _):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.apply_user_policy('policy_name', 'username', policy_statements=[MinIOPolicyStatement(['bucket'])])


@patch("subprocess.check_call")
@patch("server.minioclient.tempfile.NamedTemporaryFile", autospec=True)
@patch("subprocess.check_output", side_effect=lambda cmd: mcli_mock(cmd, "Unknownerror"))
def test_minio_apply_user_policy__unknown_error(check_output_mock, __, _):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")

    with pytest.raises(ValueError) as e:
        client.apply_user_policy('policy_name', 'username', policy_statements=[MinIOPolicyStatement(['bucket'])])

    assert "Applying policy failed: Error: Unknownerror" in str(e)


@patch("subprocess.check_call")
@patch("subprocess.check_output")
def test_minio_remove_user_policy(check_output_mock, _):
    client = MinioClient(url='http://test.invalid', user='test', secret_key='test', alias="local")
    client.remove_user_policy('policy_name', 'username')

    check_output_mock.assert_has_calls([
        call(['mcli', '--no-color', 'admin', 'policy', 'detach', 'local', 'policy_name', '--user', 'username']),
        call(['mcli', '--no-color', 'admin', 'policy', 'remove', 'local', 'policy_name'])])


def test_create_valid_bucket_name():
    # Name is too short
    assert MinioClient.create_valid_bucket_name("") == "b--x"
    assert MinioClient.create_valid_bucket_name("ab") == "b--ab"

    # Name is too long
    bucket_name = ".rhjfklsahjfkdlsahuifeohwuiafohuiofhueioahufieohauiefohuaieof-"
    assert len(MinioClient.create_valid_bucket_name(bucket_name)) == 63

    # Wrong characters
    assert MinioClient.create_valid_bucket_name("/*_~!@#$%^&*()_+|.---........") == 'x-----------------------x'

    # IP address
    assert MinioClient.create_valid_bucket_name("192.168.5.4") == "ip-192.168.5.4"
