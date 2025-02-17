import os
import sys
from decimal import Decimal

import pytest
from prosper_shared.omni_config import _realize_config_schemata, _realize_input_schemata
from prosper_shared.omni_config._define import _arg_parse_from_schema
from prosper_shared.omni_config._merge import _merge_config
from prosper_shared.omni_config._parse import _ArgParseSource

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
                "--single-run",
                "--min-bid=30",
                "--target-loan-count=600",
                "--search-for-almost-funded",
                "--analytics",
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
                "search-for-almost-funded": True,
                "analytics": True,
            }
        )
        assert config._config_dict["prosper-bot"]["cli"] == {
            "dry-run": True,
            "verbose": True,
            "single-run": True,
        }
        assert config._config_dict["prosper-api"] == {
            "auth": {"token-cache": "fake-token-cache"},
            "credentials": {
                "client-id": "0123456789abcdef0123456789abcdef",
                "username": "fake-username",
            },
        }

    @pytest.mark.xfail("CI" in os.environ, reason="The output has changed on GitHub")
    def test_cli_help(self, mocker, snapshot):
        """This test asserts that the CLI help hasn't changed so we can ensure there are no backwards-incompatible changes."""
        mocker.patch(
            "prosper_shared.omni_config._define.user_config_dir",
            lambda i: f"/config_dir/dir/{i}",
        )
        mocker.patch("prosper_shared.omni_config._define.getcwd", lambda: "/cwd/dir")
        config_schemata = _merge_config(_realize_config_schemata())
        input_schemata = _merge_config(_realize_input_schemata())
        next(
            v
            for v in config_schemata["prosper-api"]["auth"].keys()
            if v._expected_val == "token-cache"
        )._default = "/some/path/to/token-cache"
        source = _ArgParseSource(
            _arg_parse_from_schema(
                config_schemata, input_schemata, prog_name="prosper-bot"
            )
        )
        assert source._argument_parser.format_help() == snapshot
