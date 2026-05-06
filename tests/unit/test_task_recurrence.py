from datetime import date
from types import SimpleNamespace

from app.application.services.tasks import _iter_occurrence_dates
from app.domain.enums import TaskRecurrenceType


def test_daily_recurrence_jumps_to_generation_window_start():
    series = SimpleNamespace(
        starts_on=date(2020, 1, 1),
        ends_on=None,
        recurrence_type=TaskRecurrenceType.DAILY,
        recurrence_interval=1,
    )

    occurrence_dates = _iter_occurrence_dates(
        series,
        date(2026, 5, 5),
        date(2026, 5, 7),
    )

    assert occurrence_dates == [
        date(2026, 5, 5),
        date(2026, 5, 6),
        date(2026, 5, 7),
    ]


def test_monthly_recurrence_jumps_to_generation_window_and_preserves_anchor():
    series = SimpleNamespace(
        starts_on=date(2020, 1, 31),
        ends_on=None,
        recurrence_type=TaskRecurrenceType.MONTHLY,
        recurrence_interval=1,
    )

    occurrence_dates = _iter_occurrence_dates(
        series,
        date(2026, 2, 1),
        date(2026, 4, 30),
    )

    assert occurrence_dates == [
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    ]
