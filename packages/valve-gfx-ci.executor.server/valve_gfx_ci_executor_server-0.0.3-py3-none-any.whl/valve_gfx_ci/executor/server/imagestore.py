from dataclasses import field, asdict
from datetime import timedelta
from enum import StrEnum, auto
from fcntl import flock, LOCK_EX
from functools import cached_property
from hashlib import blake2b
from pathlib import Path
from pydantic.dataclasses import dataclass
from subprocess import run, CalledProcessError

import os
import string
import traceback
import time
import yaml

from . import config


# Store mounting configuration

@dataclass(config=dict(extra="forbid"))
class ImageStoreFilesystem:
    type: str
    src: str
    opts: list[str]

    def to_b2c_filesystem(self, name):
        opts = "|".join(self.opts)
        return f'b2c.filesystem={name},type={self.type},src={self.src},opts={opts}'


@dataclass(config=dict(extra="forbid"))
class ImageStoreConfig:
    mount: list[ImageStoreFilesystem] = field(default_factory=list)

    @classmethod
    def load(cls):
        with open(Path(config.IMAGESTORE_PATH) / "config.yml", "r") as f:
            return cls(**yaml.safe_load(f.read()))


def imagestore_template_resources():
    def mount(store_name) -> dict[str, ImageStoreFilesystem]:
        cfg = ImageStoreConfig.load()

        params = {}
        for fs in cfg.mount:
            # Add the store name to the src
            fs.src = f"{fs.src}/{store_name}"
            params[fs.type] = fs

        return params

    return {
        "imagestore": {
            "mount": mount
        }
    }


# Image


@dataclass
class ImagePull:
    id: str
    pulled_at: float

    @property
    def pull_age(self) -> timedelta:
        return timedelta(seconds=time.time() - self.pulled_at)


@dataclass
class ImagePullHistory:
    platforms: dict[str, ImagePull] | None = field(default_factory=dict)


class ImageStorePullPolicy(StrEnum):
    ALWAYS = auto()          # Always try pulling the image
    RELAXED_ALWAYS = auto()  # Re-use a previous pull if it is less than 5 minutes old
    MISSING = auto()         # Only pull the image if it is unknown


@dataclass(frozen=True)
class ImageStoreImage:
    store_name: str
    image_name: str
    tls_verify: bool
    platform: str
    pull_policy: ImageStorePullPolicy

    @cached_property
    def imagestore_path(self) -> Path:
        return Path(config.IMAGESTORE_PATH) / self.store_name

    @cached_property
    def image_locks_path(self) -> Path:
        return self.imagestore_path / ".ci-tron" / "locks"

    @cached_property
    def image_lock_path(self) -> Path:
        self.image_locks_path.mkdir(0o755, parents=True, exist_ok=True)

        img_hash = blake2b(self.image_name.encode(), digest_size=32).hexdigest()
        return self.image_locks_path / img_hash

    def _pull_cmd(self):
        mappings = {
            "imgstore": self.imagestore_path,
            "image_name": self.image_name,
            "tls_verify": str(self.tls_verify).lower(),
            "platform": self.platform,
            "pull": self.pull_policy,
        }
        return string.Template(config.IMAGESTORE_PULL_CMD).substitute(mappings)

    def _image_exists_cmd(self, image_id):
        mappings = {
            "imgstore": self.imagestore_path,
            "image_name": image_id,
        }
        return string.Template(config.IMAGESTORE_IMAGE_EXISTS_CMD).substitute(mappings)

    def pull(self, timeout: float = None) -> str:
        """ Return the image hash/ID associated to `image_name` for the the wanted platform """

        def get_timeout() -> float:
            return timeout - start + time.time() if timeout else None

        # If we've already pulled, re-use the image ID we got
        if hasattr(self, "image_pull"):
            return self.image_pull.id

        start = time.time()

        with os.fdopen(os.open(self.image_lock_path, os.O_RDWR | os.O_CREAT), "r+") as f:
            # Make sure to de-duplicate download requests, even when they come from multiple clients
            flock(f, LOCK_EX)

            # Parse the pull history of the image in this store
            pull_history = ImagePullHistory()
            try:
                if history := yaml.safe_load(f.read()):
                    pull_history = ImagePullHistory(**history)
            except Exception:  # pragma: nocover
                traceback.print_exc()

            # Check if we have previously queried the container registry for this image/platform
            if self.pull_policy != ImageStorePullPolicy.ALWAYS:
                image = pull_history.platforms.get(self.platform)
                if image and image.id:
                    r = run(self._image_exists_cmd(image.id), shell=True, timeout=get_timeout())

                    if r.returncode == 0:
                        # We have already queried the registry for this image on this platform, and the image is still
                        # present in our image store! Now, let's check what's our pull policy to figure out what to do
                        # next.
                        if self.pull_policy == ImageStorePullPolicy.MISSING:
                            return image.id
                        elif self.pull_policy == ImageStorePullPolicy.RELAXED_ALWAYS:
                            if image.pull_age < timedelta(minutes=5):
                                return image.id
                        else:  # pragma: nocover
                            raise ValueError("Unhandled pull policy")

            # Pull the image
            try:
                r = run(self._pull_cmd(), capture_output=True, text=True, shell=True, check=True, timeout=get_timeout())
            except CalledProcessError as e:
                raise ValueError(f"Exit code {e.returncode}, Stdout:\n{e.stdout}\n\nStderr:\n{e.stderr}") from None

            # Update the pull history
            image = ImagePull(id=r.stdout.strip(), pulled_at=time.time())
            pull_history.platforms[self.platform] = image

            # Write back the pull history
            f.seek(0, os.SEEK_SET)
            f.truncate(0)
            f.write(yaml.dump(asdict(pull_history)))

            # Keep the ImagePull cached
            object.__setattr__(self, 'image_pull', image)

            return self.image_pull.id

        # NOTE: The lock gets released here, when we close the file

    @cached_property
    def image_id(self):
        return self.pull()

    # TODO: Add a way to remove images unused for the past N days by using the create time
