# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from datetime import datetime, timedelta
from typing import List
from ._models import RecurrencePatternType, RecurrenceRangeType, Recurrence, RecurrencePattern, RecurrenceRange


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


def validate_settings(recurrence: Recurrence, start: datetime, end: datetime) -> None:
    """
    Validate the settings for the time window filter.

    :param TimeWindowFilterSettings settings: The settings for the time window filter.
    :raises ValueError: If the settings are invalid.
    """
    if not recurrence:
        raise ValueError("Recurrence is required")

    _validate_start_end_parameter(start, end)
    _validate_recurrence_pattern(recurrence.pattern, start, end)
    _validate_recurrence_range(recurrence.range, start)


def _validate_start_end_parameter(start: datetime, end: datetime) -> None:
    param_name = "end"
    if end > start + timedelta(days=TEN_YEARS):
        raise ValueError(TIME_WINDOW_DURATION_TEN_YEARS % param_name)


def _validate_recurrence_pattern(pattern: RecurrencePattern, start: datetime, end: datetime) -> None:
    pattern_type = pattern.type

    if pattern_type == RecurrencePatternType.DAILY:
        _validate_daily_recurrence_pattern(pattern, start, end)
    else:
        _validate_weekly_recurrence_pattern(pattern, start, end)


def _validate_recurrence_range(recurrence_range: RecurrenceRange, start: datetime) -> None:
    range_type = recurrence_range.type
    if range_type == RecurrenceRangeType.END_DATE:
        _validate_end_date(recurrence_range, start)


def _validate_daily_recurrence_pattern(pattern: RecurrencePattern, start: datetime, end: datetime) -> None:
    # "Start" is always a valid first occurrence for "Daily" pattern.
    # Only need to check if time window validated
    _validate_time_window_duration(pattern, start, end)


def _validate_weekly_recurrence_pattern(pattern: RecurrencePattern, start: datetime, end: datetime) -> None:
    _validate_days_of_week(pattern)

    # Check whether "Start" is a valid first occurrence
    if start.weekday() not in pattern.days_of_week:
        raise ValueError(NOT_MATCHED % start.strftime("%A"))

    # Time window duration must be shorter than how frequently it occurs
    _validate_time_window_duration(pattern, start, end)

    # Check whether the time window duration is shorter than the minimum gap between days of week
    if not _is_duration_compliant_with_days_of_week(pattern, start, end):
        raise ValueError(TIME_WINDOW_DURATION_OUT_OF_RANGE % "Recurrence.Pattern.DaysOfWeek")


def _validate_time_window_duration(pattern: RecurrencePattern, start: datetime, end: datetime) -> None:
    interval_duration = (
        timedelta(days=pattern.interval)
        if pattern.type == RecurrencePatternType.DAILY
        else timedelta(days=pattern.interval * DAYS_PER_WEEK)
    )
    time_window_duration = end - start
    if start > end:
        raise ValueError(OUT_OF_RANGE % "The filter start date Start needs to before the End date.")

    if time_window_duration > interval_duration:
        raise ValueError(TIME_WINDOW_DURATION_OUT_OF_RANGE % "Recurrence.Pattern.Interval")


def _validate_days_of_week(pattern: RecurrencePattern) -> None:
    days_of_week = pattern.days_of_week
    if not days_of_week:
        raise ValueError(REQUIRED_PARAMETER % "Recurrence.Pattern.DaysOfWeek")


def _validate_end_date(recurrence_range: RecurrenceRange, start: datetime) -> None:
    end_date = recurrence_range.end_date
    if end_date and end_date < start:
        raise ValueError("The Recurrence.Range.EndDate should be after the Start")


def _is_duration_compliant_with_days_of_week(pattern: RecurrencePattern, start: datetime, end: datetime) -> bool:
    days_of_week = pattern.days_of_week
    if len(days_of_week) == 1:
        return True

    # Get the date of first day of the week
    today = datetime.now()
    first_day_of_week = pattern.first_day_of_week
    offset = _get_passed_week_days((today.weekday() + 1) % 7, first_day_of_week)
    first_date_of_week = today - timedelta(days=offset)
    sorted_days_of_week = _sort_days_of_week(days_of_week, first_day_of_week)

    # Loop the whole week to get the min gap between the two consecutive recurrences
    prev_occurrence = first_date_of_week + timedelta(
        days=_get_passed_week_days(sorted_days_of_week[0], first_day_of_week)
    )
    min_gap = timedelta(days=DAYS_PER_WEEK)

    for day in sorted_days_of_week[1:]:
        date = first_date_of_week + timedelta(days=_get_passed_week_days(day, first_day_of_week))
        if prev_occurrence is not None:
            current_gap = date - prev_occurrence
            min_gap = min(min_gap, current_gap)
        prev_occurrence = date

    if pattern.interval == 1:
        # It may cross weeks. Check the adjacent week
        date = first_date_of_week + timedelta(
            days=DAYS_PER_WEEK + _get_passed_week_days(sorted_days_of_week[0], first_day_of_week)
        )

        current_gap = date - prev_occurrence
        min_gap = min(min_gap, current_gap)

    time_window_duration = end - start
    return min_gap >= time_window_duration


def _get_passed_week_days(current_day: int, first_day_of_week: int) -> int:
    """
    Get the number of days passed since the first day of the week.
    :param int current_day: The current day of the week, where Sunday == 0 ... Saturday == 6.
    :param int first_day_of_week: The first day of the week (0-6), where Sunday == 0 ... Saturday == 6.
    :return: The number of days passed since the first day of the week.
    :rtype: int
    """
    return (current_day - first_day_of_week + DAYS_PER_WEEK) % DAYS_PER_WEEK


def _sort_days_of_week(days_of_week: List[int], first_day_of_week: int) -> List[int]:
    sorted_days = sorted(days_of_week)
    if first_day_of_week in sorted_days:
        return sorted_days[sorted_days.index(first_day_of_week) :] + sorted_days[: sorted_days.index(first_day_of_week)]
    next_closest_day = first_day_of_week
    for i in range(7):
        if (first_day_of_week + i) % 7 in sorted_days:
            next_closest_day = (first_day_of_week + i) % 7
            break
    return sorted_days[sorted_days.index(next_closest_day) :] + sorted_days[: sorted_days.index(next_closest_day)]
