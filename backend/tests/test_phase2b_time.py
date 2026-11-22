"""Phase 2B: the UTC time helper that replaces the deprecated datetime.utcnow()."""
import warnings
from datetime import datetime, timedelta, timezone

from app.core.time import utcnow
from app.models.job import JobDescription


def test_utcnow_is_current_utc_without_timezone():
    now = utcnow()
    assert now.tzinfo is None                                  # same shape as the stored columns
    real = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(real - now) < timedelta(seconds=5)


def test_utcnow_raises_no_deprecation_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        utcnow()


def test_models_use_the_helper_for_timestamps():
    col = JobDescription.__table__.c.created_at
    assert col.default.arg.__name__ == "utcnow"
