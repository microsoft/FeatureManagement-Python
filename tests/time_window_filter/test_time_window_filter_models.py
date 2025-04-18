# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from featuremanagement._time_window_filter._models import RecurrencePatternType, RecurrenceRangeType, RecurrencePattern, RecurrenceRange, Recurrence
from datetime import datetime
import math

def test_recurrence_pattern_type():
    assert RecurrencePatternType.from_str("Daily") == RecurrencePatternType.DAILY
    assert RecurrencePatternType.from_str("Weekly") == RecurrencePatternType.WEEKLY
    try:
        RecurrencePatternType.from_str("Invalid")
    except ValueError as e:
        assert str(e) == "Invalid value: Invalid"

def test_recurrence_range_type():
    assert RecurrenceRangeType.from_str("NoEnd") == RecurrenceRangeType.NO_END
    assert RecurrenceRangeType.from_str("EndDate") == RecurrenceRangeType.END_DATE
    assert RecurrenceRangeType.from_str("Numbered") == RecurrenceRangeType.NUMBERED
    try:
        RecurrenceRangeType.from_str("Invalid")
    except ValueError as e:
        assert str(e) == "Invalid value: Invalid"

def test_recurrence_pattern():
    pattern = RecurrencePattern({"Type":"Daily", "Interval":1, "DaysOfWeek":["Monday", "Tuesday"]})
    assert pattern.type == RecurrencePatternType.DAILY
    assert pattern.interval == 1
    assert pattern.days_of_week == [0, 1]
    assert pattern.first_day_of_week == 6

    pattern = RecurrencePattern({"Type":"Daily", "Interval":1, "DaysOfWeek":["Monday", "Tuesday"], "FirstDayOfWeek":"Monday"})
    assert pattern.type == RecurrencePatternType.DAILY
    assert pattern.interval == 1
    assert pattern.days_of_week == [0, 1]
    assert pattern.first_day_of_week == 0

    try:
        pattern = RecurrencePattern({"Type":"Daily", "Interval":1, "DaysOfWeek":["Monday", "Tuesday"], "FirstDayOfWeek":"Thor's day"})
    except ValueError as e:
        assert str(e) == "Invalid value for FirstDayOfWeek: Thor's day"

    pattern = RecurrencePattern({"Type":"Weekly", "Interval":2, "DaysOfWeek":["Wednesday"]})
    assert pattern.type == RecurrencePatternType.WEEKLY
    assert pattern.interval == 2
    assert pattern.days_of_week == [2]
    assert pattern.first_day_of_week == 6

    try:
        pattern = RecurrencePattern({"Type":"Daily", "Interval":0, "DaysOfWeek":["Monday", "Tuesday"]})
    except ValueError as e:
        assert str(e) == "The interval must be greater than 0."

    try:
        pattern = RecurrencePattern({"Type":"Daily", "Interval":1, "DaysOfWeek":["Monday", "Thor's day"]})
    except ValueError as e:
        assert str(e) == "Invalid value for DaysOfWeek: Thor's day"

def test_recurrence_range():
    max_occurrences = math.pow(2, 63) - 1

    range = RecurrenceRange({"Type":"NoEnd"})
    assert range.type == RecurrenceRangeType.NO_END
    assert range.end_date is None
    assert range.num_of_occurrences == max_occurrences

    range = RecurrenceRange({"Type":"EndDate", "EndDate":"Mon, 31 Mar 2025 00:00:00"})
    assert range.type == RecurrenceRangeType.END_DATE
    assert range.end_date == datetime(2025, 3, 31, 0, 0, 0)
    assert range.num_of_occurrences == max_occurrences

    range = RecurrenceRange({"Type":"Numbered", "NumberOfOccurrences":10})
    assert range.type == RecurrenceRangeType.NUMBERED
    assert range.end_date is None
    assert range.num_of_occurrences == 10

    try:
        range = RecurrenceRange({"Type":"NoEnd", "NumberOfOccurrences":-1})
    except ValueError as e:
        assert str(e) == "The number of occurrences must be greater than or equal to 0."

    try:
        range = RecurrenceRange({"Type":"EndDate", "EndDate":"InvalidDate"})
    except ValueError as e:
        assert str(e) == "Invalid value for EndDate: InvalidDate"