from dataclasses import field
from pydantic.dataclasses import dataclass
from pydantic import model_validator

import re
import traceback
import yaml

from . import config


@dataclass(config=dict(extra="forbid"))
class ImageRewrite:
    match: str
    replace: str

    def to_local_proxy(self, image_name):
        # Remove any prefix that may not be needed
        for prefix in ["docker://", ""]:
            if image_name.startswith(prefix):
                image_name = image_name.removeprefix(prefix)
                break

        return prefix + re.sub(self.match, self.replace, image_name)

    @model_validator(mode='after')
    def is_valid_sub(self):
        try:
            re.sub(self.match, self.replace, "")
            return self
        except re.error as e:
            raise ValueError(f"The match/replace tuple is invalid: {e.msg}")


@dataclass(config=dict(extra="forbid"))
class RegistryConfig:
    image_rewrites: list[ImageRewrite] = field(default_factory=list)

    @classmethod
    def load(cls, path=None):
        try:
            with open(config.REGISTRIES_CFG, "r") as f:
                return cls(**yaml.safe_load(f.read()))
        except Exception:
            traceback.print_exc()
            return cls()

    @classmethod
    def to_local_proxy(cls, image_name: str) -> str:
        for image in cls.load().image_rewrites:
            proxied_image = image.to_local_proxy(image_name)
            if proxied_image != image_name:
                return proxied_image

        return image_name


def registry_template_resources():
    return {
        "registry": {
            "to_local_proxy": RegistryConfig.to_local_proxy,
        }
    }
