from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (occurrence - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    first_next = date(year + (month == 12), month % 12 + 1, 1)
    cursor = first_next - timedelta(days=1)
    return cursor - timedelta(days=(cursor.weekday() - weekday) % 7)


def _easter(year: int) -> date:
    """Gregorian Easter using the Meeus/Jones/Butcher algorithm."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (b - (b + 8) // 25 + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    return date(year, month, (h + ell - 7 * m + 114) % 31 + 1)


def regular_us_equity_holidays(year: int) -> set[date]:
    holidays = {
        _observed(date(year, 1, 1)),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _easter(year) - timedelta(days=2),
        _last_weekday(year, 5, 0),
        _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
        _observed(date(year, 12, 25)),
    }
    if year >= 2022:
        holidays.add(_observed(date(year, 6, 19)))
    return holidays


@dataclass(frozen=True, slots=True)
class UsEquityCalendar:
    exceptional_closures: frozenset[date] = frozenset()
    exceptional_openings: frozenset[date] = frozenset()

    def is_session(self, day: date) -> bool:
        if day in self.exceptional_openings:
            return True
        return (
            day.weekday() < 5
            and day not in regular_us_equity_holidays(day.year)
            and day not in self.exceptional_closures
        )

    def sessions(self, start: date, end: date) -> list[date]:
        if end < start:
            raise ValueError("end cannot precede start")
        return [
            start + timedelta(days=i)
            for i in range((end - start).days + 1)
            if self.is_session(start + timedelta(days=i))
        ]

    def next_session(self, day: date) -> date:
        cursor = day + timedelta(days=1)
        while not self.is_session(cursor):
            cursor += timedelta(days=1)
        return cursor

    def close_timestamp(self, day: date, early_close: bool = False) -> datetime:
        if not self.is_session(day):
            raise ValueError(f"{day} is not a trading session")
        local_close = datetime.combine(day, time(13 if early_close else 16), tzinfo=NEW_YORK)
        return local_close.astimezone(UTC)


def missing_sessions(observed: list[date], calendar: UsEquityCalendar) -> list[date]:
    if not observed:
        return []
    expected = set(calendar.sessions(min(observed), max(observed)))
    return sorted(expected - set(observed))
