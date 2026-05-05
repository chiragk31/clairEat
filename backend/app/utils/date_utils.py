"""
ClairEat — Timezone-Aware Date Utilities
"""

from datetime import date, datetime, timezone
from typing import Optional
import pytz


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def today_utc() -> date:
    """Return today's date in UTC."""
    return utcnow().date()


def today_in_tz(tz_name: str) -> date:
    """Return today's date in the user's local timezone.

    Falls back to UTC if the timezone name is unrecognised.
    """
    try:
        tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        tz = pytz.utc
    return datetime.now(tz=tz).date()


def iso(dt: datetime) -> str:
    """Format a datetime as ISO 8601 string."""
    return dt.isoformat()


def parse_date(value: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD) into a date object."""
    return date.fromisoformat(value)


def date_range(start: date, days: int) -> list[date]:
    """Return a list of *days* consecutive dates starting from *start*."""
    from datetime import timedelta
    return [start + timedelta(days=i) for i in range(days)]


def format_date(d: date) -> str:
    """Format a date as YYYY-MM-DD string."""
    return d.isoformat()


def week_start(d: Optional[date] = None) -> date:
    """Return the Monday of the week containing *d* (or today)."""
    from datetime import timedelta
    d = d or today_utc()
    return d - timedelta(days=d.weekday())
