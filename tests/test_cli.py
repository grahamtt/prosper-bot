import sys
from decimal import Decimal

import pytest

from prosper_bot.cli import build_config


class TestCli:
    def test_build_config_defaults(self, mocker):
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
                "min-bid": Decimal("25"),
                "strategy": "AGGRESSIVE",
                "simulate": False,
            }
        )
        assert config._config_dict["cli"] == {"dry-run": False, "verbose": False}
        assert config._config_dict["credentials"] == {
            "client-id": "0123456789abcdef0123456789abcdef",
            "username": "fake-username",
        }
        assert config._config_dict["auth"]["token-cache"] == "fake-token-cache"

    def test_build_config(self, mocker):
        mocker.patch.object(
            sys,
            "argv",
            [
                "test-cli",
                "--client-id=0123456789abcdef0123456789abcdef",
                "--username=fake-username",
                "--token-cache=fake-token-cache",
                "--dry-run",
                "--verbose",
                "--min-bid=30",
                "--strategy=CONSERVATIVE",
            ],
        )

        config = build_config()

        assert config._config_dict["bot"] == pytest.approx(
            {
                "min-bid": Decimal("30"),
                "strategy": "CONSERVATIVE",
                "simulate": False,
            }
        )
        assert config._config_dict["cli"] == {"dry-run": True, "verbose": True}
        assert config._config_dict["credentials"] == {
            "client-id": "0123456789abcdef0123456789abcdef",
            "username": "fake-username",
        }
        assert config._config_dict["auth"]["token-cache"] == "fake-token-cache"
