from decimal import Decimal

import pytest

from prosper_bot.bot.bot import Bot


class TestBot:
    @pytest.mark.parametrize(
        ["input", "expected_output"],
        [
            (Decimal("0"), None),
            (Decimal("24.99"), None),
            (Decimal("25.00"), Decimal("25.00")),
            (Decimal("25.01"), Decimal("25.01")),
            (Decimal("49.99"), Decimal("49.99")),
            (Decimal("50.00"), Decimal("25.00")),
            (Decimal("50.01"), Decimal("25.01")),
        ],
    )
    def test__get_bid_amount(self, input, expected_output):
        assert Bot._get_bid_amount(input) == expected_output
