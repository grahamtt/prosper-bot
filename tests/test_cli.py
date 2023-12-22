import sys
from decimal import Decimal

import pytest

from prosper_bot.allocation_strategy.fixed_target import (
    FixedTargetAllocationStrategyTargets,
)
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

        assert config._config_dict["prosper_bot"]["bot"] == pytest.approx(
            {
                "min-bid": Decimal("25"),
                "strategy": FixedTargetAllocationStrategyTargets.AGGRESSIVE,
            }
        )
        assert config._config_dict["prosper_bot"]["cli"] == {
            "dry-run": False,
            "verbose": False,
            "simulate": False,
        }
        assert config._config_dict["prosper_api"] == {
            "auth": {"token-cache": "fake-token-cache"},
            "credentials": {
                "client-id": "0123456789abcdef0123456789abcdef",
                "username": "fake-username",
            },
        }
        assert config._config_dict["prosper_shared"] == {
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

        assert config._config_dict["prosper_bot"]["bot"] == pytest.approx(
            {
                "min-bid": Decimal("30"),
                "strategy": FixedTargetAllocationStrategyTargets.CONSERVATIVE,
            }
        )
        assert config._config_dict["prosper_bot"]["cli"] == {
            "dry-run": True,
            "verbose": True,
            "simulate": False,
        }
        assert config._config_dict["prosper_api"] == {
            "auth": {"token-cache": "fake-token-cache"},
            "credentials": {
                "client-id": "0123456789abcdef0123456789abcdef",
                "username": "fake-username",
            },
        }
        assert config._config_dict["prosper_shared"] == {
            "serde": {"parse-dates": True, "parse-enums": True, "use-decimals": True}
        }
