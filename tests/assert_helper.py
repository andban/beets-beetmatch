import pytest


def assert_almost_equal(actual, expected, decimals=7):
    __tracebackhide__ = True
    if round(actual, decimals) != expected:
        pytest.fail(f"actual {actual} almost equal to {expected}")


def assert_greater_than(actual, expected):
    __tracebackhide__ = True
    if not (actual > expected):
        pytest.fail(f"actual {actual} greater than {expected}")
