import sys
from decimal import Decimal

import pytest

from prosper_bot.cli import build_config


class TestCli:
    def test_build_config(self, mocker):
        mocker.patch.object(
            sys,
            "argv",
            [
                "test-cli",
                "--client-id=0123456789abcdef0123456789abcdef",
                "--username=fake-username",
                "--token-cache=fake-token-cache",
            ],
        )

        config = build_config()

        assert config._config_dict["bot"] == pytest.approx(
            {
                "dry-run": False,
                "min-bid": Decimal("25"),
                "verbose": False,
            }
        )
        assert config._config_dict["credentials"] == {
            "client-id": "0123456789abcdef0123456789abcdef",
            "username": "fake-username",
        }
        assert config._config_dict["auth"]["token-cache"] == "fake-token-cache"
