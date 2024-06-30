import sys
from decimal import Decimal

import pytest

from prosper_bot.allocation_strategy import AllocationStrategies
from prosper_bot.bot import bot
from prosper_bot.cli import build_config


class TestCli:
    # Ensure the schema is loaded
    bot._schema()

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
                "--target-loan-count=600"
                # TODO: the --strategy param is broken :(
                # "--strategy=CONSERVATIVE",
            ],
        )

        config = build_config()

        assert config._config_dict["prosper-bot"]["bot"] == pytest.approx(
            {
                "min-bid": Decimal("30"),
                "strategy": AllocationStrategies.AGGRESSIVE,
                "target-loan-count": 600,
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
