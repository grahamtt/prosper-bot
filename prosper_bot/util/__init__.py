import logging
from decimal import Decimal
from numbers import Number
from typing import Any, Callable, Dict, Hashable, Iterable

import black

logger = logging.getLogger(__file__)


def repr_lambda(v: Any):
    """Intended to be able to get the raw representation of an object including the source of a lambda."""
    # if callable(v):
    #     return next(src_line for src_line in inspect.getsourcelines(v) if "lambda: " in src_line).replace(r".*lambda:", "lambda:")
    #
    # if isinstance(v, dict):
    #     return '{' + ', '.join(f"{k}: {repr_lambda(v)}" for k,v in v.items()) + '}'
    #
    # if isinstance(v, (list, tuple, set)):
    #     str_val = ', '.join(repr_lambda(v) for v in v)
    #     if isinstance(v, list):
    #         return '[' + str_val + ']'
    #     if isinstance(v, tuple):
    #         return '(' + str_val + ')'
    #     if isinstance(v, set):
    #         return '{' + str_val + '}'

    return repr(v)


def ppprint(o: Any) -> str:
    """Uses `black` to pretty-print Python objects.

    Arguments:
        o (Any): A raw Python value

    Returns:
        str: A formatted string representation of the value
    """
    return black.format_file_contents(repr_lambda(o), fast=False, mode=black.Mode())


def bucketize(
    input: Iterable[Any],
    bucketizer: Callable[[Any], Hashable] = lambda v: v,
    evaluator: Callable[[Any], Number] = lambda v: 1,
) -> Dict[Hashable, Number]:
    """Method to bucketize a series of values.

    Transforms a sequence of values into a dict of buckets where the bucket key is calculated using the provided `bucketizer`
    (the individual items by default) and the value summed is calculated using the provided `evaluator` (the count by default).
    The dict is sorted by the keys before returning.

    Arguments:
        input (Iterable[Any]): the collection of items to bucketize.
        bucketizer (Callable[[Any], Hashable]): A method to extract the key from the provided items. Defaults to return the item itself.
        evaluator (Callable[[Any], Number]): A method to extract the value from the provided items. Defaults to return a count of the items.

    Returns:
        Dict[Hashable, Number]: The result of summing the values into the calculated buckets.
    """
    unsorted_result = {}
    for item in input:
        bucket = bucketizer(item)
        value = evaluator(item)
        if bucket in unsorted_result:
            unsorted_result[bucket] += value
        else:
            unsorted_result[bucket] = value

    try:
        sorted_result = {k: unsorted_result[k] for k in sorted(unsorted_result.keys())}
    except TypeError:
        logger.warning("Sorting histogram by key failed; falling back to unsorted")
        sorted_result = unsorted_result

    return sorted_result


def print_histogram(
    title: str,
    histogram: Dict[Hashable, Number],
    percent: bool = True,
    printer: Callable[[str], object] = print,
):
    """Prints a string representation of a dict representing a histogram.

    Arguments:
        title (str): The title to print for the histogram.
        histogram (Dict[Hashable, Number]): The key/value pairs to render as a histogram.
        percent (bool): Whether the values should be converted to percentages of the total before rendering. Defaults to True.
        printer (Callable[[str], object]): The method to use to print, for example `logger.info`. Defaults to `print`.
    """
    max_len = max(len(str(key)) for key in histogram.keys())
    total = sum(histogram.values())
    printer(f"### {title} ###")
    for key, val in histogram.items():
        scaled_val = val / total * 100 if percent else val
        printer(
            f"{key:{max_len}}: {'#'*int(scaled_val)} {scaled_val:3.2f}{'%' if percent else ''}"
        )


def round_down_to_nearest_cent(amount: Decimal):
    """Round down the given amount to the nearest cent."""
    rounded_amount = amount.quantize(Decimal(".01"), rounding="ROUND_DOWN")
    logging.debug(f"Rounded down ${amount} to nearest cent: ${rounded_amount}")
    return rounded_amount
