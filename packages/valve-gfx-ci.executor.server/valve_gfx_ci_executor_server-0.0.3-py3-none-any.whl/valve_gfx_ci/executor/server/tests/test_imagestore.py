import pytest
import time
import yaml

from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch, MagicMock

from server.imagestore import ImageStoreConfig, ImageStoreFilesystem, imagestore_template_resources
from server.imagestore import ImageStoreImage, ImageStorePullPolicy, ImagePull, ImagePullHistory
import server.config as config


def test_ImageStoreFilesystem__to_b2c_filesystem():
    cfg = ImageStoreFilesystem(type="nfs", src="10.0.0.1:/nfs", opts=['opt1', 'opt2'])

    assert cfg.to_b2c_filesystem("myFS") == "b2c.filesystem=myFS,type=nfs,src=10.0.0.1:/nfs,opts=opt1|opt2"


def test_ImageStoreConfig(tmpdir):
    config.IMAGESTORE_PATH = tmpdir

    # Write down the original config
    orig_cfg = ImageStoreConfig(mount=[
        ImageStoreFilesystem(type="nfs", src="10.0.0.1:/nfs", opts=['opt1', 'opt2']),
        ImageStoreFilesystem(type="ceph", src="10.0.0.1:/ceph", opts=['opt3', 'opt4']),
    ])
    (Path(config.IMAGESTORE_PATH) / "config.yml").write_text(yaml.dump(asdict(orig_cfg)))

    # Reload the config, and compare the original one
    assert ImageStoreConfig.load() == orig_cfg

    # Check the generated imagestore template resources
    assert imagestore_template_resources()["imagestore"]["mount"]("mystore") == {
        "nfs": ImageStoreFilesystem(type="nfs", src="10.0.0.1:/nfs/mystore", opts=['opt1', 'opt2']),
        "ceph": ImageStoreFilesystem(type="ceph", src="10.0.0.1:/ceph/mystore", opts=['opt3', 'opt4']),
    }


img = ImageStoreImage(store_name="private", platform="linux/riscv64", tls_verify=False,
                      image_name="registry.freedesktop.org/gfx-ci/ci-tron/gateway:latest",
                      pull_policy=ImageStorePullPolicy.ALWAYS)


def test_ImagePull():
    pull_img = ImagePull(id="", pulled_at=time.time())

    assert pull_img.pull_age < timedelta(seconds=1)
    assert pull_img.pull_age > timedelta(seconds=0)


def test_ImageStoreImage_image_lock_path(tmpdir: Path):
    config.IMAGESTORE_PATH = tmpdir

    # Verify that the imagestore path is in the tmpdir and finishes by the store name
    assert img.imagestore_path.is_absolute()
    assert str(img.imagestore_path).startswith(str(tmpdir))
    assert img.imagestore_path.name == img.store_name

    # Verify that the locks path path is in the tmpdir and finishes by the store name
    assert img.image_locks_path.is_absolute()
    assert str(img.image_locks_path).startswith(str(img.imagestore_path))
    assert img.image_locks_path.parts[-2:] == (".ci-tron", "locks")

    # Make sure accessing the lock path creates the parent's folder
    assert not img.image_locks_path.exists()
    assert img.image_lock_path.parent == img.image_locks_path
    assert img.image_locks_path.exists()


def test_ImageStoreImage__commands():
    img = ImageStoreImage(store_name="private", platform="linux/riscv64", tls_verify=False,
                          image_name="registry.freedesktop.org/gfx-ci/ci-tron/gateway:latest",
                          pull_policy=ImageStorePullPolicy.ALWAYS)

    config.IMAGESTORE_PATH = "/cache/imagestores/"
    assert img._pull_cmd() == ("podman --root /cache/imagestores/private pull --tls-verify=false "
                               "--platform=linux/riscv64 registry.freedesktop.org/gfx-ci/ci-tron/gateway:latest")
    assert img._image_exists_cmd("image_name") == "podman --root /cache/imagestores/private image exists image_name"


def do_pull(run_mock, tmpdir, pull_policy, platform="platform", timeout=None):
    config.IMAGESTORE_PATH = tmpdir
    img = ImageStoreImage(store_name="private", image_name="image", tls_verify=True, platform=platform,
                          pull_policy=pull_policy)
    img.pull(timeout=timeout)

    pull_history = ImagePullHistory()
    with open(img.image_lock_path) as f:
        if history := yaml.safe_load(f.read()):
            pull_history = ImagePullHistory(**history)

    return img, pull_history


@patch("server.imagestore.run", return_value=MagicMock(returncode=0, stdout="image_id"))
def test_ImageStoreImage__imageid_full_lifecycle(run_mock, tmpdir):
    cur_time = time.time()

    # Initial pull
    with patch('server.imagestore.time.time', return_value=cur_time):
        img, pull_history = do_pull(run_mock, tmpdir, pull_policy=ImageStorePullPolicy.ALWAYS, platform="platform",
                                    timeout=1)
    run_mock.assert_called_once_with(img._pull_cmd(), capture_output=True, text=True, shell=True, check=True,
                                     timeout=1)
    assert pull_history == ImagePullHistory(platforms={"platform": ImagePull(id="image_id", pulled_at=cur_time)})

    # Ensure we do not re-use the image for another platform
    run_mock.reset_mock()
    with patch('server.imagestore.time.time', return_value=cur_time + 1):
        img, pull_history = do_pull(run_mock, tmpdir, pull_policy=ImageStorePullPolicy.MISSING, platform="new_platform")
    run_mock.assert_called_once_with(img._pull_cmd(), capture_output=True, text=True, shell=True, check=True,
                                     timeout=None)
    assert pull_history == ImagePullHistory(platforms={
        "platform": ImagePull(id="image_id", pulled_at=cur_time),
        "new_platform": ImagePull(id="image_id", pulled_at=cur_time + 1),
    })

    # Try reusing an image using the RELAXED_ALWAYS policy
    run_mock.reset_mock()
    with patch('server.imagestore.time.time', return_value=cur_time + 299):  # Add 4 minutes and 59 seconds
        img, pull_history = do_pull(run_mock, tmpdir, pull_policy=ImageStorePullPolicy.RELAXED_ALWAYS,
                                    platform="platform")
    run_mock.assert_called_once_with(img._image_exists_cmd("image_id"), shell=True, timeout=None)
    assert img.image_id == "image_id"
    assert pull_history.platforms['platform'].pulled_at == cur_time

    # Try reusing an image using the RELAXED_ALWAYS policy, after expiration
    run_mock.reset_mock()
    with patch('server.imagestore.time.time', return_value=cur_time + 300):  # Add 5 minutes
        img, pull_history = do_pull(run_mock, tmpdir, pull_policy=ImageStorePullPolicy.RELAXED_ALWAYS,
                                    platform="platform")
    assert run_mock.call_count == 2
    run_mock.assert_any_call(img._image_exists_cmd("image_id"), shell=True, timeout=None)
    run_mock.assert_any_call(img._pull_cmd(), capture_output=True, text=True, shell=True, check=True,
                             timeout=None)
    assert img.image_id == "image_id"
    assert pull_history.platforms['platform'].pulled_at == cur_time + 300

    # Try reusing an image using the MISSING policy
    run_mock.reset_mock()
    with patch('server.imagestore.time.time', return_value=cur_time + 300):
        img, pull_history = do_pull(run_mock, tmpdir, pull_policy=ImageStorePullPolicy.MISSING,
                                    platform="new_platform")
    run_mock.assert_called_once_with(img._image_exists_cmd("image_id"), shell=True, timeout=None)
    assert img.image_id == "image_id"
    assert pull_history.platforms['new_platform'].pulled_at == cur_time + 1


@patch("server.imagestore.run", return_value=MagicMock(stdout="image_id"))
def test_ImageStoreImage__imageid_pull__fail(run_mock, tmpdir):
    run_mock.side_effect = CalledProcessError(returncode=42, cmd="", output="stdout", stderr="stderr")
    with pytest.raises(ValueError) as exc:
        do_pull(run_mock, tmpdir, pull_policy=ImageStorePullPolicy.ALWAYS)

    assert 'Exit code 42, Stdout:\nstdout\n\nStderr:\nstderr' in str(exc.value)
