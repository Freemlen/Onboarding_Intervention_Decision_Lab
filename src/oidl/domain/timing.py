"""Integer pre-assignment clocks and support mapping: DGP §§4.1–4.3."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import math

from .contracts import ContractError
from .design import OFFSETS, PERIODS, SHIFTS

SECOND = 1_000_000
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
LOCK_TS = 35 * DAY
EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


def require_fraction(u):
    if type(u) not in (float, int) or not math.isfinite(u) or not 0 <= u <= 1:
        raise ContractError("PRE_OUTCOME_TIME", "INVALID_FRACTION")


def require_integer_time(t):
    if type(t) is not int:
        raise ContractError("PRE_OUTCOME_TIME", "INTEGER_MICROSECONDS_REQUIRED")


def tick(a, b, u):
    require_integer_time(a)
    require_integer_time(b)
    require_fraction(u)
    if b <= a:
        raise ContractError("PRE_OUTCOME_TIME", "EMPTY_REQUIRED_SUPPORT")
    m = b - a
    return a + 1 + min(m - 1, math.floor(u * m))


@dataclass(frozen=True, slots=True)
class CallingSegment:
    lower: int
    upper: int
    lower_inclusive: bool
    upper_inclusive: bool

    @property
    def duration(self):
        return self.upper - self.lower


def calling_segments(registration_ts, offset_hours):
    """Continuous intersections, retaining the frozen open/closed endpoints."""
    require_integer_time(registration_ts)
    if type(offset_hours) is not int or offset_hours not in OFFSETS:
        raise ContractError("PRE_OUTCOME_TIME", "INVALID_FIXED_UTC_OFFSET")
    t0 = registration_ts + 12 * HOUR
    deadline = registration_ts + 24 * HOUR - 15 * MINUTE
    offset = offset_hours * HOUR
    first_day = (t0 + offset) // DAY
    last_day = (deadline + offset) // DAY
    segments = []
    for day in range(first_day, last_day + 1):
        opening = day * DAY + 9 * HOUR - offset
        closing = day * DAY + 20 * HOUR - offset
        lo, hi = max(t0, opening), min(deadline, closing)
        if hi > lo:
            segments.append(CallingSegment(lo, hi, opening > t0, deadline < closing))
    return tuple(segments)


def calling_window_available(registration_ts, offset_hours):
    return any(s.duration >= 30 * MINUTE for s in calling_segments(registration_ts, offset_hours))


def shift_contains(local_second, shift):
    if shift == "DAY":
        return 10 * 3600 <= local_second < 16 * 3600
    if shift == "EVENING":
        return 16 * 3600 <= local_second < 23 * 3600
    if shift == "NIGHT":
        return local_second >= 23 * 3600 or local_second < 7 * 3600
    raise ContractError("PRE_OUTCOME_TIME", "INVALID_REGISTRATION_SHIFT")


@lru_cache(maxsize=1)
def _callable_local_seconds():
    return frozenset(
        second for second in range(86_400)
        if calling_window_available(second * SECOND, 0)
    )


@lru_cache(maxsize=16, typed=True)
def registration_daily_support(shift, offset_hours, callable_required=True):
    if type(offset_hours) is not int or offset_hours not in OFFSETS:
        raise ContractError("PRE_OUTCOME_TIME", "INVALID_FIXED_UTC_OFFSET")
    if type(callable_required) is not bool:
        raise ContractError("PRE_OUTCOME_TIME", "BOOLEAN_SUPPORT_FLAG_REQUIRED")
    if (callable_required and shift not in SHIFTS) or (not callable_required and shift is not None):
        raise ContractError("PRE_OUTCOME_TIME", "SHIFT_APPLICABILITY_MISMATCH")
    callable_seconds = _callable_local_seconds()
    selected = []
    for utc_second in range(86_400):
        local = (utc_second + offset_hours * 3600) % 86_400
        if callable_required:
            include = local in callable_seconds and shift_contains(local, shift)
        else:
            include = local not in callable_seconds
        if include:
            selected.append(utc_second)
    if not selected:
        raise ContractError("PRE_OUTCOME_TIME", "EMPTY_REQUIRED_SUPPORT")
    return tuple(selected)


def registration_from_fraction(period, shift, offset_hours, u, callable_required=True):
    """Cumulative rank in the full seven-day sorted set, without rejection sampling."""
    require_fraction(u)
    if period not in PERIODS:
        raise ContractError("PRE_OUTCOME_TIME", "INVALID_REGISTRATION_PERIOD")
    daily = registration_daily_support(shift, offset_hours, callable_required)
    size = 7 * len(daily)
    index = min(size - 1, math.floor(u * size))
    day, within = divmod(index, len(daily))
    return (PERIODS.index(period) * 7 + day) * DAY + daily[within] * SECOND


def period_at(registration_ts):
    require_integer_time(registration_ts)
    if not 0 <= registration_ts < 28 * DAY:
        raise ContractError("PRE_OUTCOME_TIME", "REGISTRATION_OUTSIDE_INTAKE")
    return PERIODS[registration_ts // (7 * DAY)]


def utc_timestamp(t):
    require_integer_time(t)
    return (EPOCH + timedelta(microseconds=t)).isoformat(timespec="microseconds").replace("+00:00", "Z")
