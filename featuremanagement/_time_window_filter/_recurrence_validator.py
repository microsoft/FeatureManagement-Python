# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from datetime import datetime, timedelta
from typing import List
from ._models import RecurrencePatternType, RecurrenceRangeType, TimeWindowFilterSettings


DAYS_PER_WEEK = 7
TEN_YEARS = 3650
RECURRENCE_PATTERN = "Pattern"
RECURRENCE_PATTERN_DAYS_OF_WEEK = "DaysOfWeek"
RECURRENCE_RANGE = "Range"
REQUIRED_PARAMETER = "Required parameter: %s"
OUT_OF_RANGE = "Out of range: %s"
TIME_WINDOW_DURATION_TEN_YEARS = "Time window duration exceeds ten years: %s"
NOT_MATCHED = "Start day does not match any day of the week: %s"
TIME_WINDOW_DURATION_OUT_OF_RANGE = "Time window duration is out of range: %s"


def validate_settings(settings: TimeWindowFilterSettings) -> None:
    """
    Validate the settings for the time window filter.

    :param TimeWindowFilterSettings settings: The settings for the time window filter.
    :raises ValueError: If the settings are invalid.
    """
    _validate_recurrence_required_parameter(settings)
    _validate_recurrence_pattern(settings)
    _validate_recurrence_range(settings)


def _validate_recurrence_required_parameter(settings: TimeWindowFilterSettings) -> None:
    recurrence = settings.recurrence
    param_name = ""
    reason = ""
    if recurrence.pattern is None:
        param_name = f"{RECURRENCE_PATTERN}"
        reason = REQUIRED_PARAMETER
    if recurrence.range is None:
        param_name = f"{RECURRENCE_RANGE}"
        reason = REQUIRED_PARAMETER
    if not settings.end > settings.start:
        param_name = "end"
        reason = OUT_OF_RANGE
    if settings.end > settings.start + timedelta(days=TEN_YEARS):
        param_name = "end"
        reason = TIME_WINDOW_DURATION_TEN_YEARS

    if param_name:
        raise ValueError(reason % param_name)


def _validate_recurrence_pattern(settings: TimeWindowFilterSettings) -> None:
    pattern_type = settings.recurrence.pattern.type

    if pattern_type == RecurrencePatternType.DAILY:
        _validate_daily_recurrence_pattern(settings)
    else:
        _validate_weekly_recurrence_pattern(settings)


def _validate_recurrence_range(settings: TimeWindowFilterSettings) -> None:
    range_type = settings.recurrence.range.type
    if range_type == RecurrenceRangeType.END_DATE:
        _validate_end_date(settings)


def _validate_daily_recurrence_pattern(settings: TimeWindowFilterSettings) -> None:
    # "Start" is always a valid first occurrence for "Daily" pattern.
    # Only need to check if time window validated
    _validate_time_window_duration(settings)


def _validate_weekly_recurrence_pattern(settings: TimeWindowFilterSettings) -> None:
    _validate_days_of_week(settings)

    # Check whether "Start" is a valid first occurrence
    pattern = settings.recurrence.pattern
    if settings.start.weekday() not in pattern.days_of_week:
        raise ValueError(NOT_MATCHED % "start")

    # Time window duration must be shorter than how frequently it occurs
    _validate_time_window_duration(settings)

    # Check whether the time window duration is shorter than the minimum gap between days of week
    if not _is_duration_compliant_with_days_of_week(settings):
        raise ValueError(TIME_WINDOW_DURATION_OUT_OF_RANGE % "Recurrence.Pattern.DaysOfWeek")


def _validate_time_window_duration(settings: TimeWindowFilterSettings) -> None:
    pattern = settings.recurrence.pattern
    interval_duration = (
        timedelta(days=pattern.interval)
        if pattern.type == RecurrencePatternType.DAILY
        else timedelta(days=pattern.interval * DAYS_PER_WEEK)
    )
    time_window_duration = settings.end - settings.start
    if time_window_duration > interval_duration:
        raise ValueError(TIME_WINDOW_DURATION_OUT_OF_RANGE % "Recurrence.Pattern.Interval")


def _validate_days_of_week(settings: TimeWindowFilterSettings) -> None:
    days_of_week = settings.recurrence.pattern.days_of_week
    if not days_of_week:
        raise ValueError(REQUIRED_PARAMETER % "Recurrence.Pattern.DaysOfWeek")


def _validate_end_date(settings: TimeWindowFilterSettings) -> None:
    end_date = settings.recurrence.range.end_date
    if end_date and end_date < settings.start:
        raise ValueError("The Recurrence.Range.EndDate should be after the Start")


def _is_duration_compliant_with_days_of_week(settings: TimeWindowFilterSettings) -> bool:
    days_of_week = settings.recurrence.pattern.days_of_week
    if len(days_of_week) == 1:
        return True

    # Get the date of first day of the week
    today = datetime.now()
    first_day_of_week = settings.recurrence.pattern.first_day_of_week
    offset = _get_passed_week_days(today.weekday(), first_day_of_week)
    first_date_of_week = today - timedelta(days=offset)
    sorted_days_of_week = _sort_days_of_week(days_of_week, first_day_of_week)

    # Loop the whole week to get the min gap between the two consecutive recurrences
    prev_occurrence = None
    min_gap = timedelta(days=DAYS_PER_WEEK)

    for day in sorted_days_of_week:
        date = first_date_of_week + timedelta(days=_get_passed_week_days(day, first_day_of_week))
        if prev_occurrence is not None:
            current_gap = date - prev_occurrence
            min_gap = min(min_gap, current_gap)
        prev_occurrence = date

    if settings.recurrence.pattern.interval == 1:
        # It may cross weeks. Check the adjacent week
        date = first_date_of_week + timedelta(
            days=DAYS_PER_WEEK + _get_passed_week_days(sorted_days_of_week[0], first_day_of_week)
        )

        if not prev_occurrence:
            return False

        current_gap = date - prev_occurrence
        min_gap = min(min_gap, current_gap)

    time_window_duration = settings.end - settings.start
    return min_gap >= time_window_duration


def _get_passed_week_days(today: int, first_day_of_week: int) -> int:
    return (today - first_day_of_week + DAYS_PER_WEEK) % DAYS_PER_WEEK


def _sort_days_of_week(days_of_week: List[int], first_day_of_week: int) -> List[int]:
    sorted_days = sorted(days_of_week, key=lambda day: _get_passed_week_days(day, first_day_of_week))
    return sorted_days
