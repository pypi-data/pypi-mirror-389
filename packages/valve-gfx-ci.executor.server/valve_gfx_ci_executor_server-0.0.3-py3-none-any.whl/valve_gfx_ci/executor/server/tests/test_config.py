from unittest.mock import patch
import pytest

import server.config as config


@patch("server.config.socket.gethostname")
def test_get_farm_name_from_hostname(gethostname_mock):
    gethostname_mock.return_value = "unformated_name"
    assert config.get_farm_name_from_hostname() is None

    gethostname_mock.return_value = "testfarm-gateway"
    assert config.get_farm_name_from_hostname() == "testfarm"


def test_as_boolean():
    try:
        # Check for the conditions to be true
        for value in [' eNaBlEd  ', ' tRuE ', "1 ", 1, True]:
            config.TEST_AS_BOOLEAN = value
            assert config.as_boolean("TEST_AS_BOOLEAN")

        # Check for the conditions to be false
        for value in [' dIsAbLeD  ', ' FaLsE ', "  0 ", 0, False]:
            config.TEST_AS_BOOLEAN = value
            assert not config.as_boolean("TEST_AS_BOOLEAN")

        # Check that any other value is considered invalid
        for value in [None, "data", 42, ""]:
            config.TEST_AS_BOOLEAN = value

            with pytest.raises(ValueError) as exc:
                config.as_boolean("TEST_AS_BOOLEAN")

            assert "is not an accepted boolean" in str(exc)
    finally:
        del config.TEST_AS_BOOLEAN
