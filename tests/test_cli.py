import sys
from decimal import Decimal

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

        assert config._config_dict["bot"] == {
            "dry-run": False,
            "min-bid": Decimal("25"),
            "verbose": False,
        }
        assert config._config_dict["credentials"] == {
            "client-id": "f3c747293f3e4dc5a27a6ff3cf4f6805",
            "username": "fake-username",
        }
        assert config._config_dict["auth"]["token-cache"] is not None
