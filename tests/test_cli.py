import sys

from prosper_bot.cli import build_config


class TestCli:
    def test_build_config(self, mocker):
        mocker.patch.object(sys, "argv", [])

        build_config()
