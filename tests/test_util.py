import pytest

from prosper_bot.util import bucketize


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
