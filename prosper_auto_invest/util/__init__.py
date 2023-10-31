import logging
from numbers import Number
from typing import List, Callable, Dict, Hashable, Iterable, Any

import black


logger = logging.getLogger(__file__)


def ppprint(o):
    return black.format_str(repr(o), mode=black.Mode())


def bucketize(
    input: Iterable[Any],
    bucketizer: Callable[[Any], Hashable] = lambda v: v,
    evaluator: Callable[[Any], Number] = lambda v: 1,
) -> Dict[Hashable, Number]:
    """
    Transforms a sequence of values into a dict of buckets where the bucket key is calculated using the provided `bucketizer`
    (the individual items by default) and the value summed is calculated using the provided `evaluator` (the count by default).
    The dict is sorted by the keys before returning.
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
    percent=True,
    printer: Callable[[str], object] = print,
):
    max_len = max(len(str(key)) for key in histogram.keys())
    total = sum(histogram.values())
    printer(f"### {title} ###")
    for key, val in histogram.items():
        scaled_val = val / total * 100 if percent else val
        printer(
            f"{key:{max_len}}: {'#'*int(scaled_val)} {scaled_val:3.2f}{'%' if percent else ''}"
        )
