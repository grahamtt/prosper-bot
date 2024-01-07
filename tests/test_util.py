import datetime
from decimal import Decimal

import pytest

from prosper_bot.util import bucketize, ppprint, print_histogram


class TestUtils:
    @pytest.mark.parametrize(
        ["iterable", "expected"],
        [
            ([3, 5, 7, 3, 8, 1, 1], {1: 2, 3: 2, 5: 1, 7: 1, 8: 1}),
            (
                ["a", "e", "3", "7", "ab", "a"],
                {"a": 2, "ab": 1, "e": 1, "3": 1, "7": 1},
            ),
            (["a", "e", "3", 7, "ab", "a"], {"a": 2, "ab": 1, "e": 1, "3": 1, 7: 1}),
            ([1, 1, 1, 1, 1, 2, 2, 2, 2, 2], {1: 5, 2: 5}),
            ([1, 2, 1, 2, 1, 2, 1, 2, 1, 2], {1: 5, 2: 5}),
        ],
    )
    def test_bucketize_when_defaults_used(self, iterable, expected):
        assert bucketize(iterable) == expected

    @pytest.mark.parametrize(
        ["iterable", "bucketizer", "expected"],
        [
            ([{"a": 3}, {"a": 5}], lambda v: v["a"], {3: 1, 5: 1}),
            ([{"a": 3}, {"a": 5, "b": 7}], lambda v: v["a"], {3: 1, 5: 1}),
        ],
    )
    def test_bucketize_with_custom_bucketizer(self, iterable, bucketizer, expected):
        assert bucketize(iterable, bucketizer) == expected

    @pytest.mark.parametrize(
        ["iterable", "bucketizer", "evaluator", "expected"],
        [
            ([{"a": 3}, {"a": 3}], lambda v: v["a"], lambda v: v["a"], {3: 6}),
            (
                [{"a": 3, "b": 3}, {"a": 3, "b": 2}],
                lambda v: v["a"],
                lambda v: v["b"],
                {3: 5},
            ),
            (
                [{"a": 3, "b": 3}, {"a": 3, "b": 2}, {"a": 5, "b": 2}],
                lambda v: v["a"],
                lambda v: v["b"],
                {3: 5, 5: 2},
            ),
        ],
    )
    def test_bucketize_with_custom_bucketizer_and_evaluator(
        self, iterable, bucketizer, evaluator, expected
    ):
        assert bucketize(iterable, bucketizer, evaluator) == expected

    def test_print_histogram_percent(self, mocker):
        printer = mocker.MagicMock()
        print_histogram(
            "Title", {"a": 6, "b": 9, "c": 3}, percent=True, printer=printer
        )

        assert printer.mock_calls == [
            mocker.call("### Title ###"),
            mocker.call("a: ################################# 33.33%"),
            mocker.call("b: ################################################## 50.00%"),
            mocker.call("c: ################ 16.67%"),
        ]

    def test_print_histogram_not_percent(self, mocker):
        printer = mocker.MagicMock()
        print_histogram(
            "Title", {"a": 6, "b": 9, "c": 3}, percent=False, printer=printer
        )

        assert printer.mock_calls == [
            mocker.call("### Title ###"),
            mocker.call("a: ###### 6.00"),
            mocker.call("b: ######### 9.00"),
            mocker.call("c: ### 3.00"),
        ]

    def test_ppprint(self):
        assert ppprint(
            {
                "dateval": datetime.datetime(2024, 1, 6, 13, 37, 45, 510548),
                # "lambdaval": lambda: 45,
                "dictval": {"k1": "v1", "k2": "v2"},
                "intval": 1234,
                "floatval": 1234.5678,
                "decimalval": Decimal("1234.5678"),
            }
        ) == (
            "{\n"
            '    "dateval": datetime.datetime(2024, 1, 6, 13, 37, 45, 510548),\n'
            '    "dictval": {"k1": "v1", "k2": "v2"},\n'
            '    "intval": 1234,\n'
            '    "floatval": 1234.5678,\n'
            '    "decimalval": Decimal("1234.5678"),\n'
            "}\n"
        )
