import pytest
import tempfile
import yaml

from dataclasses import asdict

from server.registry import ImageRewrite, RegistryConfig, registry_template_resources
import server.config as config


fdo_proxy = ImageRewrite(match=r"^registry.freedesktop.org", replace="ci-gateway:8002")
quay_proxy = ImageRewrite(match=r"^quay.io", replace="ci-gateway:8100")
project_proxy = ImageRewrite(match=r"^registry.gitlab.com/(gfx-ci/ci-tron/.+)$", replace=r"ci-gateway:8101/\1")

cfg = RegistryConfig(image_rewrites=[fdo_proxy, quay_proxy, project_proxy])


def test_Image__image_name_matched_return_proxied_name():
    # Ensure the prefix has no impact on the matching
    for prefix in ["docker://", ""]:
        img_name = prefix + "registry.freedesktop.org/gfx-ci/ci-tron/gateway:latest"
        assert fdo_proxy.to_local_proxy(img_name) == f"{prefix}{fdo_proxy.replace}/gfx-ci/ci-tron/gateway:latest"

    assert (project_proxy.to_local_proxy("registry.gitlab.com/gfx-ci/ci-tron/helloworld:latest") ==
            "ci-gateway:8101/gfx-ci/ci-tron/helloworld:latest")


def test_Image__image_name_not_matched_return_original_name():
    assert quay_proxy.to_local_proxy("docker://alpine:latest") == "docker://alpine:latest"


def test_ImageRewrite__invalid_regexes():
    with pytest.raises(ValueError) as exc:
        ImageRewrite(match=r"+registry.freedesktop.org", replace="ci-gateway:8002")

    assert "The match/replace tuple is invalid" in str(exc)


def test_RegistryConfig__without_config_returns_empty():
    assert RegistryConfig.load() == RegistryConfig()


def test_RegistryConfig__with_valid_config():
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        config.REGISTRIES_CFG = fp.name

        fp.write(yaml.dump(asdict(cfg)))
        fp.flush()

        # Reload the config, and compare the original one
        assert RegistryConfig.load() == cfg

        # Check the generated imagestore template resources
        img = "docker://quay.io/alpine:latest"
        assert cfg.to_local_proxy(img) == "docker://ci-gateway:8100/alpine:latest"
        assert cfg.to_local_proxy("alpine:latest") == "alpine:latest"


def test_registry_template_resources():
    assert registry_template_resources()["registry"]["to_local_proxy"] == RegistryConfig.to_local_proxy
