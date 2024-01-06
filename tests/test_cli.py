import sys
from decimal import Decimal

import pytest

from prosper_bot.allocation_strategy import AllocationStrategies
from prosper_bot.bot import bot
from prosper_bot.cli import build_config


class TestCli:
    # Ensure the schema is loaded
    bot._schema()

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

        assert config._config_dict["prosper-bot"]["bot"] == pytest.approx(
            {
                "min-bid": Decimal("25"),
                "strategy": AllocationStrategies.AGGRESSIVE,
            }
        )
        assert config._config_dict["prosper-bot"]["cli"] == {
            "dry-run": False,
            "verbose": False,
        }
        assert config._config_dict["prosper-api"] == {
            "auth": {"token-cache": "fake-token-cache"},
            "credentials": {
                "client-id": "0123456789abcdef0123456789abcdef",
                "username": "fake-username",
            },
        }
        assert config._config_dict["prosper-shared"] == {
            "serde": {"parse-dates": True, "parse-enums": True, "use-decimals": True}
        }

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

        assert config._config_dict["prosper-bot"]["bot"] == pytest.approx(
            {
                "min-bid": Decimal("30"),
                "strategy": AllocationStrategies.CONSERVATIVE,
            }
        )
        assert config._config_dict["prosper-bot"]["cli"] == {
            "dry-run": True,
            "verbose": True,
        }
        assert config._config_dict["prosper-api"] == {
            "auth": {"token-cache": "fake-token-cache"},
            "credentials": {
                "client-id": "0123456789abcdef0123456789abcdef",
                "username": "fake-username",
            },
        }
        assert config._config_dict["prosper-shared"] == {
            "serde": {"parse-dates": True, "parse-enums": True, "use-decimals": True}
        }
