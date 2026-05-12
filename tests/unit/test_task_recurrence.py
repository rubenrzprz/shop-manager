from datetime import date
from types import SimpleNamespace

from app.application.services.tasks import _iter_occurrence_dates
from app.domain.enums import TaskMonthlyRecurrenceRule, TaskRecurrenceType


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


def test_monthly_recurrence_supports_last_day_rule():
    series = SimpleNamespace(
        starts_on=date(2026, 1, 10),
        ends_on=None,
        recurrence_type=TaskRecurrenceType.MONTHLY,
        recurrence_interval=1,
        monthly_rule=TaskMonthlyRecurrenceRule.LAST_DAY_OF_MONTH,
    )

    occurrence_dates = _iter_occurrence_dates(
        series,
        date(2026, 1, 1),
        date(2026, 3, 31),
    )

    assert occurrence_dates == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    ]


def test_monthly_recurrence_supports_first_day_rule():
    series = SimpleNamespace(
        starts_on=date(2026, 1, 10),
        ends_on=None,
        recurrence_type=TaskRecurrenceType.MONTHLY,
        recurrence_interval=1,
        monthly_rule=TaskMonthlyRecurrenceRule.FIRST_DAY_OF_MONTH,
    )

    occurrence_dates = _iter_occurrence_dates(
        series,
        date(2026, 1, 1),
        date(2026, 3, 31),
    )

    assert occurrence_dates == [
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


def test_monthly_recurrence_supports_specific_day_rule():
    series = SimpleNamespace(
        starts_on=date(2026, 1, 10),
        ends_on=None,
        recurrence_type=TaskRecurrenceType.MONTHLY,
        recurrence_interval=1,
        monthly_rule=TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH,
        monthly_day=31,
    )

    occurrence_dates = _iter_occurrence_dates(
        series,
        date(2026, 1, 1),
        date(2026, 3, 31),
    )

    assert occurrence_dates == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    ]
