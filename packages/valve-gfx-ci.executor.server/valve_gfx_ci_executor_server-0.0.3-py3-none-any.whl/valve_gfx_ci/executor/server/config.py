import os
import socket
import tempfile
from pathlib import Path

BASE_DIR = os.path.dirname(__file__)


def template(filename):
    return os.path.join(os.path.join(BASE_DIR, 'templates'), filename)


def job_template(filename):
    return os.path.join(os.path.join(BASE_DIR, 'job_templates'), filename)


def get_farm_name_from_hostname():
    hostname = socket.gethostname()

    # Recognize the format: $FARM_NAME-gateway
    farm_name = hostname.removesuffix('-gateway')
    if hostname != farm_name:
        return farm_name

    return None


def as_boolean(key):
    value = str(globals().get(key, "")).strip().lower()

    if value in ["true", "enabled", "1"]:
        return True
    elif value in ["false", "disabled", "0"]:
        return False
    else:
        raise ValueError((f"The value '{value}' is not an accepted boolean. "
                          "Accepted values: true/false, enabled/disabled, 1/0"))


# Note: Don't forget to update /documentation/docs/executor.rst
executor_root = Path(tempfile.gettempdir())
configurables = {
    'CONSOLE_PATTERN_DEFAULT_MACHINE_UNFIT_FOR_SERVICE_REGEX': None,
    'EXECUTOR_URL': 'http://ci-gateway',
    'EXECUTOR_HOST': '0.0.0.0',
    'EXECUTOR_PORT': 80,
    'EXECUTOR_HTTP_IPv4_SOCKET_NAME': 'http_ipv4',
    'EXECUTOR_REGISTRATION_JOB': job_template('register.yml.j2'),
    'EXECUTOR_BOOTLOOP_JOB': job_template('bootloop.yml.j2'),
    'EXECUTOR_VPDU_ENDPOINT': None,
    'EXECUTOR_ARTIFACT_CACHE_ROOT': executor_root / "artifact_cache",
    'EXECUTOR_NBD_ROOT': executor_root / "nbd",
    'SERGENT_HARTMAN_BOOT_COUNT': '100',
    'SERGENT_HARTMAN_QUALIFYING_BOOT_COUNT': '100',
    'SERGENT_HARTMAN_REGISTRATION_RETRIAL_DELAY': '120',
    'SERGENT_HARTMAN_QUICK_CHECK': 'enabled',
    'SERGENT_HARTMAN_QUIET': 'false',
    'GITLAB_CONF_FILE': '/etc/gitlab-runner/config.toml',
    'GITLAB_CONF_TEMPLATE_FILE': template('gitlab_runner_config.toml.j2'),
    'GITLAB_ALLOW_INSECURE': 'false',
    'GITLAB_RUNNER_PATH': '/usr/bin/gitlab-runner',
    'GITHUB_RUNNER_PATH': '/usr/share/github-runner-template/run.sh',
    'FARM_NAME': get_farm_name_from_hostname(),
    'MARS_DB_FILE': '/config/mars_db.yaml',
    'BOOTS_DB_USER_FILE': '/config/boots_db.yml.j2',
    'BOOTS_DB_FILE': template('boots_db.yml.j2'),
    'SALAD_URL': 'http://ci-gateway:8005',
    'BOOTS_DISABLE_SERVERS': None,
    'MINIO_URL': 'http://ci-gateway:9000',
    'MINIO_ROOT_USER': 'minioadmin',
    'MINIO_ROOT_PASSWORD': 'minio-root-password',
    'MINIO_ADMIN_ALIAS': 'local',
    'PRIVATE_INTERFACE': 'private',
    'BOOTS_DHCP_IPv4_SOCKET_NAME': 'dhcp_ipv4',
    'BOOTS_TFTP_IPv4_SOCKET_NAME': 'tftp_ipv4',
    'IMAGESTORE_PATH': Path(tempfile.gettempdir()) / 'imagestores/',
    'IMAGESTORE_PULL_CMD':
        'podman --root ${imgstore} pull --tls-verify=${tls_verify} --platform=${platform} ${image_name}',
    'IMAGESTORE_IMAGE_EXISTS_CMD': 'podman --root ${imgstore} image exists ${image_name}',
    'REGISTRIES_CFG': Path(tempfile.gettempdir()) / 'registries' / 'config.yml',
    'DUT_DEFAULT_BOOT_SEQUENCE_POWER': 10,
}
# Note: Don't forget to update /documentation/docs/executor.rst

__all__ = []


for config_option, default in configurables.items():
    globals()[config_option] = os.environ.get(config_option,
                                              default)
    __all__.append(config_option)


def job_environment_vars() -> dict[str, str]:  # pragma: nocover
    """Return environment variables useful for job submission as a
    dictionary."""

    ret = {
        'MINIO_URL': globals()['MINIO_URL'],
    }

    for var, val in os.environ.items():
        if var.startswith('EXECUTOR_JOB__'):
            ret[var.removeprefix('EXECUTOR_JOB__')] = val

    return ret
