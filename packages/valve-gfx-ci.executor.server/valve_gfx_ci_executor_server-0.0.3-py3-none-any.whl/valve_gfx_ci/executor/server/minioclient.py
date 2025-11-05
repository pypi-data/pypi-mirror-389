from urllib.parse import urlparse
from dataclasses import dataclass, field
from collections import defaultdict
from tarfile import TarFile
from minio import Minio
from minio.helpers import check_bucket_name
from minio.error import S3Error

import subprocess
import struct
import traceback
import ipaddress
import tempfile
import json
import re

from . import config
from .logger import logger


@dataclass
class MinIOPolicyStatement:
    # NOTE: Using the default factory to avoid mutable defaults
    buckets: list[str] = field(default_factory=lambda: ["*"])
    actions: list[str] = field(default_factory=lambda: ["s3:*"])
    allow: bool = True

    # Conditions
    source_ips: list[str] = None
    not_source_ips: list[str] = None


def generate_policy(statements):
    def nesteddict():
        return defaultdict(nesteddict)

    rendered_statements = []
    for s in statements:
        resources = [f"arn:aws:s3:::{b}" for b in s.buckets]
        resources.extend([f"arn:aws:s3:::{b}/*" for b in s.buckets])

        statement = {
            'Action': s.actions,
            'Effect': "Allow" if s.allow else "Deny",
            'Resource': resources,
        }

        conditions = nesteddict()
        if s.source_ips and len(s.source_ips) > 0:
            conditions["IpAddress"]["aws:SourceIp"] = s.source_ips
        if s.not_source_ips and len(s.not_source_ips) > 0:
            conditions["NotIpAddress"]["aws:SourceIp"] = s.not_source_ips
        if len(conditions) > 0:
            statement["Condition"] = conditions

        rendered_statements.append(statement)

    return {
        "Version": "2012-10-17",
        "Statement": rendered_statements
    }


# TODO: rename the methods to be on the form $object_$operation
# to make auto-completion work more efficiently.
class MinioClient():
    @classmethod
    def __log_mcli_error(cls, e):
        logger.error(f"""Call failed:
Command output:
{e.output}

Backtrace:
{traceback.format_exc()}
""")

    def __mcli_exec(self, args):
        assert self.alias is not None

        try:
            return subprocess.check_output(["mcli", "--no-color"] + args)
        except subprocess.CalledProcessError as e:  # pragma: nocover
            self.__log_mcli_error(e)
            raise e from None

    def __init__(self,
                 url=config.MINIO_URL,
                 user=config.MINIO_ROOT_USER,
                 secret_key=config.MINIO_ROOT_PASSWORD,
                 alias=config.MINIO_ADMIN_ALIAS,
                 artifact_cache_root=config.EXECUTOR_ARTIFACT_CACHE_ROOT):
        self.url = url
        self.user = user
        self.secret_key = secret_key
        self.alias = alias
        self.artifact_cache_root = artifact_cache_root

        self._client = Minio(
            endpoint=urlparse(url).netloc,
            access_key=user,
            secret_key=secret_key,
            secure=False,
        )

        # Some operations can only be used using the commandline tool,
        # so initialize it
        if alias is not None:
            try:
                subprocess.check_call(
                    ["mcli", "--no-color", "alias", "set", self.alias, url,
                     self.user, self.secret_key])
            except subprocess.CalledProcessError as e:  # pragma: nocover
                self.__log_mcli_error(e)
                raise ValueError("Invalid MinIO credentials") from None

    def remove_alias(self):
        if self.alias is not None:
            self.__mcli_exec(["alias", "rm", self.alias])

    def _build_mc_attrs_str(self, tarball_member):
        ti = tarball_member.get_info()
        m = tarball_member
        # Unfortunately mc uses non-portable Go encodings in their public protocol:
        #   https://pkg.go.dev/io/fs#FileMode
        # They shouldn't do that, instead only the least
        # significant 9 bits of the go FileMode structure should be
        # exposed (the UNIX permissions). This is reality however, so
        # we need to deal with the fact they don't do it like that,
        # and try our best.  Currently mc ignores the non-standard
        # bits at least, but be a little defensive in case they change
        # their minds.
        gomode = 0
        if m.isdir():
            gomode |= 1 << 31
        if m.islnk():
            gomode |= 1 << 27
        if m.isdev():
            gomode |= 1 << 26
        if m.isfifo():
            gomode |= 1 << 25
        if m.ischr():
            gomode |= 1 << 21
        if m.isreg():
            gomode |= 1 << 15
        # Low 9-bits for file mode
        gomode |= m.mode
        # Yes, they pack is little-endian over the network.
        mode = int.from_bytes(struct.pack('<I', gomode), byteorder='little')
        return f"gid:{ti['gid']}/gname:{ti['gname']}/mode:{mode}/mtime:{int(ti['mtime'])}/uid:{ti['uid']}/uname:{ti['uname']}"  # noqa

    def extract_archive(self, archive_fileobj, bucket_name):
        with TarFile.open(fileobj=archive_fileobj, mode='r') as archive:
            while (member := archive.next()) is not None:
                # Ignore everything that isn't a file
                if not member.isfile():
                    continue
                metadata = {
                    'X-Amz-Meta-Mc-Attrs': self._build_mc_attrs_str(member)
                }
                self._client.put_object(bucket_name, member.name, archive.extractfile(member),
                                        member.size, num_parallel_uploads=1, metadata=metadata)

    def make_bucket(self, bucket_name):
        try:
            self._client.make_bucket(bucket_name)
        except S3Error:
            raise ValueError("The bucket already exists") from None

    def bucket_exists(self, bucket_name):
        return self._client.bucket_exists(bucket_name)

    # NOTE: Using minioclient's remove_bucket requires first to empty the
    # bucket. Use the CLI version for now.
    def remove_bucket(self, bucket_name):
        self.__mcli_exec(["rb", "--force", f'{self.alias}/{bucket_name}'])

    def add_user(self, user_id, password):
        self.__mcli_exec(["admin", "user", "add", self.alias, user_id, password])

    def remove_user(self, user_id):
        self.__mcli_exec(["admin", "user", "remove", self.alias, user_id])

    def groups_user_is_in(self, user_id=None):
        if user_id is None:
            user_id = self.user

        try:
            output = self.__mcli_exec(["--json", "admin", "user", "info", self.alias, user_id])
        except subprocess.CalledProcessError:  # pragma: nocover
            raise ValueError("Failed to query information about the user") from None

        # Parse the output
        groups = set()
        for g in json.loads(output).get('memberOf', []):
            if isinstance(g, str):
                # Original format: List of strings
                groups.add(g)
            elif isinstance(g, dict):
                # Current format: List of dicts
                if name := g.get("name"):
                    groups.add(name)

        return groups

    def add_user_to_group(self, user_id, group_name):
        self.__mcli_exec(["admin", "group", "add", self.alias, group_name, user_id])

    def apply_user_policy(self, policy_name, user_id, policy_statements):
        with tempfile.NamedTemporaryFile(suffix='json') as f:
            policy = generate_policy(policy_statements)
            f.write(json.dumps(policy).encode())
            f.flush()

            self.__mcli_exec(["admin", "policy", "create", self.alias, policy_name, f.name])

            try:
                self.__mcli_exec(["--json", "admin", "policy", "attach", self.alias, policy_name, "--user", user_id])
            except subprocess.CalledProcessError as e:
                data = json.loads(e.output)
                error_code = data.get("error", {}).get("cause", {}).get("error", {}).get("Code")
                if error_code not in ["XMinioPolicyAlreadyAttached"]:
                    raise ValueError(f"Applying policy failed: Error: {error_code}") from None

    def remove_user_policy(self, policy_name, user_id):
        self.__mcli_exec(["admin", "policy", "detach", self.alias, policy_name, "--user", user_id])
        self.__mcli_exec(["admin", "policy", "remove", self.alias, policy_name])

    @classmethod
    def create_valid_bucket_name(cls, base_name):
        # Bucket names can consist only of lowercase letters, numbers, dots (.), and hyphens (-)
        name = base_name.lower()
        name = re.sub(r'[^a-z0-9\-\.]', '-', name)

        # Bucket name must not contain invalid successive chars ['..', '.-', '-.']
        # NOTE: The transformation is repeated until no such sequence may be found
        while True:
            name_before_sub = name
            name = re.sub(r'(\.\.|\.-|-\.)', '-', name)
            if name == name_before_sub:
                break

        # Bucket names must be between 3 and 63 characters long.
        if len(name) < 3:
            name = "b--" + name

        # Bucket names must begin and end with a letter or number.
        # Bucket names can't begin with xn-- (for buckets created after February 2020)
        if name.startswith('xn--') or name[0] == '.' or name[0] == '-':
            name = 'x' + name

        # Bucket names must not be formatted as an IP address (for example, 192.168.5.4)
        try:
            ipaddress.ip_address(name)

            # The name is an ip address, add a prefix!
            name = "ip-" + name
        except ValueError:
            # The name isn't an IP address, all is good!
            pass

        # Bucket names must be between 3 and 63 characters long.
        name = name[0:63]

        # Bucket names must begin and end with a letter or number.
        if name[-1] == '.' or name[-1] == '-':
            name = name[0:62] + 'x'

        # Do the final checks
        check_bucket_name(name)

        return name
