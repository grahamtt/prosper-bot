from datetime import timedelta
from decimal import Decimal

import pytest
from prosper_shared.omni_config import Config

from prosper_bot.bot import bot
from prosper_bot.bot.bot import Bot


class TestBot:
    @pytest.fixture
    def client_mock(self, mocker):
        return mocker.patch("prosper_bot.bot.bot.Client")

    @pytest.mark.parametrize(
        ["input", "min_bid", "expected_output"],
        [
            # Min bid = 25
            (Decimal("0"), Decimal("25"), Decimal("0")),
            (Decimal("24.99"), Decimal("25"), Decimal("0")),
            (Decimal("25.00"), Decimal("25"), Decimal("25.00")),
            (Decimal("25.01"), Decimal("25"), Decimal("25.01")),
            (Decimal("49.99"), Decimal("25"), Decimal("49.99")),
            (Decimal("50.00"), Decimal("25"), Decimal("25.00")),
            (Decimal("50.01"), Decimal("25"), Decimal("25.01")),
            # Min bid = 30
            (Decimal("50.00"), Decimal("30"), Decimal("50.00")),
            (Decimal("59.99"), Decimal("30"), Decimal("59.99")),
            (Decimal("60.00"), Decimal("30"), Decimal("30.00")),
            (Decimal("60.01"), Decimal("30"), Decimal("30.01")),
            (Decimal("55.11"), Decimal("27.56"), Decimal("55.11")),
            (Decimal("55.12"), Decimal("27.56"), Decimal("27.56")),
            (Decimal("55.13"), Decimal("27.56"), Decimal("27.57")),
        ],
    )
    def test__get_bid_amount(self, input: Decimal, min_bid: Decimal, expected_output):
        assert Bot._get_bid_amount(input, min_bid) == expected_output

    @pytest.mark.timeout("5")
    def test_run_when_exception(self, mocker, client_mock):
        botty = Bot(Config({}))
        do_run_mock = mocker.spy(botty, "_do_run")
        mocker.patch.object(bot, "POLL_TIME", timedelta(milliseconds=10))
        do_run_mock.side_effect = [
            Exception("Should be caught"),
            KeyboardInterrupt("This should do it"),
        ]

        botty.run()

        do_run_mock.assert_has_calls([mocker.call(None), mocker.call(None)])
