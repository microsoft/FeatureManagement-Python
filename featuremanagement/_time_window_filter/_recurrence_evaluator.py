# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from datetime import datetime, timedelta
from typing import Optional
from ._models import RecurrencePatternType, RecurrenceRangeType, TimeWindowFilterSettings, OccurrenceInfo, Recurrence
from ._recurrence_validator import validate_settings, _get_passed_week_days, _sort_days_of_week

DAYS_PER_WEEK = 7
REQUIRED_PARAMETER = "Required parameter: %s"


def is_match(settings: TimeWindowFilterSettings, now: datetime) -> bool:
    """
    Check if the current time is within the time window filter settings.

    :param TimeWindowFilterSettings settings: The settings for the time window filter.
    :param datetime now: The current time.
    :return: True if the current time is within the time window filter settings, otherwise False.
    :rtype: bool
    """
    recurrence = settings.recurrence
    if recurrence is None:
        raise ValueError(REQUIRED_PARAMETER % "Recurrence")

    start = settings.start
    end = settings.end
    if start is None or end is None:
        raise ValueError(REQUIRED_PARAMETER % "Start or End")

    validate_settings(recurrence, start, end)

    previous_occurrence = _get_previous_occurrence(recurrence, start, now)
    if previous_occurrence is None:
        return False

    occurrence_end_date = previous_occurrence + (end - start)
    return now < occurrence_end_date


def _get_previous_occurrence(recurrence: Recurrence, start: datetime, now: datetime) -> Optional[datetime]:
    if now < start:
        return None

    pattern_type = recurrence.pattern.type
    if pattern_type == RecurrencePatternType.DAILY:
        occurrence_info = _get_daily_previous_occurrence(recurrence, start, now)
    elif pattern_type == RecurrencePatternType.WEEKLY:
        occurrence_info = _get_weekly_previous_occurrence(recurrence, start, now)

    recurrence_range = recurrence.range
    range_type = recurrence_range.type
    previous_occurrence = occurrence_info.previous_occurrence
    end_date = recurrence_range.end_date
    if (
        range_type == RecurrenceRangeType.END_DATE
        and previous_occurrence is not None
        and end_date is not None
        and previous_occurrence > end_date
    ):
        return None
    if (
        range_type == RecurrenceRangeType.NUMBERED
        and recurrence_range.num_of_occurrences is not None
        and occurrence_info.num_of_occurrences > recurrence_range.num_of_occurrences
    ):
        return None

    return occurrence_info.previous_occurrence


def _get_daily_previous_occurrence(recurrence: Recurrence, start: datetime, now: datetime) -> OccurrenceInfo:
    interval = recurrence.pattern.interval
    num_of_occurrences = (now - start).days // interval
    previous_occurrence = start + timedelta(days=num_of_occurrences * interval)
    return OccurrenceInfo(previous_occurrence, num_of_occurrences + 1)


def _get_weekly_previous_occurrence(recurrence: Recurrence, start: datetime, now: datetime) -> OccurrenceInfo:
    pattern = recurrence.pattern
    interval = pattern.interval
    first_day_of_first_week = start - timedelta(days=_get_passed_week_days(start.weekday(), pattern.first_day_of_week))

    number_of_interval = (now - first_day_of_first_week).days // (interval * DAYS_PER_WEEK)
    first_day_of_most_recent_occurring_week = first_day_of_first_week + timedelta(
        days=number_of_interval * (interval * DAYS_PER_WEEK)
    )
    sorted_days_of_week = _sort_days_of_week(pattern.days_of_week, pattern.first_day_of_week)
    max_day_offset = _get_passed_week_days(sorted_days_of_week[-1], pattern.first_day_of_week)
    min_day_offset = _get_passed_week_days(sorted_days_of_week[0], pattern.first_day_of_week)
    num_of_occurrences = number_of_interval * len(sorted_days_of_week) - sorted_days_of_week.index(start.weekday())

    if now > first_day_of_most_recent_occurring_week + timedelta(days=DAYS_PER_WEEK):
        num_of_occurrences += len(sorted_days_of_week)
        most_recent_occurrence = first_day_of_most_recent_occurring_week + timedelta(days=max_day_offset)
        return OccurrenceInfo(most_recent_occurrence, num_of_occurrences)

    day_with_min_offset = first_day_of_most_recent_occurring_week + timedelta(days=min_day_offset)
    if start > day_with_min_offset:
        num_of_occurrences = 0
        day_with_min_offset = start
    if now < day_with_min_offset:
        most_recent_occurrence = (
            first_day_of_most_recent_occurring_week
            - timedelta(days=interval * DAYS_PER_WEEK)
            + timedelta(days=max_day_offset)
        )
    else:
        most_recent_occurrence = day_with_min_offset
        num_of_occurrences += 1

        for day in sorted_days_of_week[sorted_days_of_week.index(day_with_min_offset.weekday()) + 1 :]:
            day_with_min_offset = first_day_of_most_recent_occurring_week + timedelta(
                days=_get_passed_week_days(day, pattern.first_day_of_week)
            )
            if now < day_with_min_offset:
                break
            most_recent_occurrence = day_with_min_offset
            num_of_occurrences += 1

    return OccurrenceInfo(most_recent_occurrence, num_of_occurrences)
