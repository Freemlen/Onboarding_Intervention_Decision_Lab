"""Fabricated clock fixtures; no post-assignment event generation."""

import math

import pytest

from oidl.domain.contracts import ContractError
from oidl.domain.design import OFFSETS, SHIFTS
from oidl.domain.timing import (
    DAY, HOUR, MINUTE, SECOND, calling_segments, calling_window_available,
    period_at, registration_daily_support, registration_from_fraction,
    shift_contains, tick, utc_timestamp,
)


@pytest.mark.parametrize("r,expected", [
    (7 * HOUR + 30 * MINUTE, True),
    (7 * HOUR + 30 * MINUTE + 1, False),
    (8 * HOUR, False),
    (9 * HOUR + 45 * MINUTE - 1, False),
    (9 * HOUR + 45 * MINUTE, True),
    (10 * HOUR, True),
])
@pytest.mark.parametrize("offset", OFFSETS)
def test_continuous_calling_window_boundaries(r, expected, offset):
    assert calling_window_available(DAY + r - offset * HOUR, offset) is expected


def test_contract_ten_am_window_and_endpoint_flags():
    (segment,) = calling_segments(10 * HOUR, 0)
    assert segment.lower == DAY + 9 * HOUR
    assert segment.upper == DAY + 9 * HOUR + 45 * MINUTE
    assert segment.lower_inclusive is True and segment.upper_inclusive is True
    (at_t0,) = calling_segments(7 * HOUR + 30 * MINUTE, 0)
    assert at_t0.duration == 30 * MINUTE
    assert at_t0.lower_inclusive is False and at_t0.upper_inclusive is False


@pytest.mark.parametrize("offset", OFFSETS)
@pytest.mark.parametrize("shift", SHIFTS + (None,))
def test_whole_second_sorted_support_and_period_endpoints(offset, shift):
    callable_required = shift is not None
    support = registration_daily_support(shift, offset, callable_required)
    assert support == tuple(sorted(set(support)))
    # Inspect every supported second with an independent interval-intersection predicate.
    for second in support:
        local = (second + offset * 3600) % 86400
        t0, deadline = local + 12 * 3600, local + 24 * 3600 - 900
        length = max(
            max(0, min(deadline, day * 86400 + 20 * 3600) - max(t0, day * 86400 + 9 * 3600))
            for day in range(3)
        )
        assert (length >= 1800) is callable_required
        if shift is not None:
            assert shift_contains(local, shift)
    for period_index, period in enumerate(("P1", "P2", "P3", "P4")):
        start = period_index * 7 * DAY
        assert registration_from_fraction(period, shift, offset, 0, callable_required) == start + support[0] * SECOND
        assert registration_from_fraction(period, shift, offset, 1, callable_required) == start + 6 * DAY + support[-1] * SECOND
        midpoint = registration_from_fraction(period, shift, offset, 0.5, callable_required)
        assert period_at(midpoint) == period and midpoint % SECOND == 0


def test_tick_exact_endpoints_and_utc_format():
    assert tick(100, 110, 0) == 101
    assert tick(100, 110, 0.5) == 106
    assert tick(100, 110, 1) == 110
    assert utc_timestamp(0) == "2000-01-01T00:00:00.000000Z"
    assert utc_timestamp(1) == "2000-01-01T00:00:00.000001Z"


@pytest.mark.parametrize("u", [-1, 1.01, math.inf, -math.inf, math.nan, True, "0.5"])
def test_invalid_fractions_fail_without_repair(u):
    with pytest.raises(ContractError):
        tick(0, 100, u)
    with pytest.raises(ContractError):
        registration_from_fraction("P1", "DAY", 0, u)


@pytest.mark.parametrize("a,b", [(1, 1), (2, 1), (False, 2), (1.0, 2)])
def test_impossible_tick_support_is_hard_failure(a, b):
    with pytest.raises(ContractError):
        tick(a, b, 0.5)


def test_invalid_calendar_and_applicability():
    for t in (-1, 28 * DAY, 1.0):
        with pytest.raises(ContractError):
            period_at(t)
    for shift, offset, callable_required in (("DAY", 0, False), (None, 0, True), ("DAY", 4, True)):
        with pytest.raises(ContractError):
            registration_daily_support(shift, offset, callable_required)


def test_cached_support_does_not_accept_boolean_as_integer_offset():
    registration_daily_support("DAY", 0, True)  # Warm the valid cache entry.
    with pytest.raises(ContractError, match="INVALID_FIXED_UTC_OFFSET"):
        registration_daily_support("DAY", False, True)
    with pytest.raises(ContractError, match="BOOLEAN_SUPPORT_FLAG_REQUIRED"):
        registration_daily_support("DAY", 0, 1)
