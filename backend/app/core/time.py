"""One place for "now", in UTC.

datetime.utcnow() is deprecated since Python 3.12 (it produced thousands of warnings in the
test run). This returns the same value - the current UTC time without a timezone attached -
so it stays compatible with the existing DateTime columns, which store naive UTC values.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
