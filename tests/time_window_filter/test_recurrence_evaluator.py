# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from datetime import datetime
import pytest
from featuremanagement._time_window_filter._recurrence_evaluator import is_match
from featuremanagement._time_window_filter._models import TimeWindowFilterSettings, Recurrence


def test_is_match_within_time_window():
    start = datetime(2025, 4, 7, 9, 0, 0)
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 8, 10, 0, 0)

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    assert is_match(settings, now) is True


def test_is_match_outside_time_window():
    start = datetime(2025, 4, 7, 9, 0, 0)
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 7, 18, 0, 0)

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    assert is_match(settings, now) is False


def test_is_match_no_previous_occurrence():
    start = datetime(2025, 4, 7, 9, 0, 0)
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 6, 10, 0, 0)  # Before the start time

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    assert is_match(settings, now) is False


def test_is_match_no_recurrence():
    start = datetime(2025, 4, 7, 9, 0, 0)
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 7, 10, 0, 0)

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=None)

    with pytest.raises(ValueError, match="Required parameter: Recurrence"):
        is_match(settings, now)


def test_is_match_missing_start():
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 7, 10, 0, 0)

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=None, end=end, recurrence=recurrence)

    with pytest.raises(ValueError, match="Required parameter: Start or End"):
        is_match(settings, now)


def test_is_match_missing_end():
    start = datetime(2025, 4, 7, 9, 0, 0)
    now = datetime(2025, 4, 7, 10, 0, 0)

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=None, recurrence=recurrence)

    with pytest.raises(ValueError, match="Required parameter: Start or End"):
        is_match(settings, now)


def test_is_match_weekly_recurrence():
    start = datetime(2025, 4, 7, 9, 0, 0)  # Monday
    end = datetime(2025, 4, 7, 17, 0, 0)  # Monday
    now = datetime(2025, 4, 14, 10, 0, 0)  # Next Monday

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Weekly", "Interval": 1, "DaysOfWeek": ["Monday"], "FirstDayOfWeek": "Monday"},
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    assert is_match(settings, now) is True


def test_is_match_end_date_has_passed():
    start = datetime(2025, 4, 7, 9, 0, 0)
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 9, 10, 0, 0)  # After the end date

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "EndDate", "EndDate": "Tue, 8 Apr 2025 10:00:00"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    assert is_match(settings, now) is False


def test_is_match_numbered_recurrence():
    start = datetime(2025, 4, 7, 9, 0, 0)
    end = datetime(2025, 4, 7, 17, 0, 0)
    now = datetime(2025, 4, 8, 10, 0, 0)

    recurrence = Recurrence(
        {
            "Pattern": {"Type": "Daily", "Interval": 1},
            "Range": {"Type": "Numbered", "NumberOfOccurrences": 2},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    assert is_match(settings, now) is True
    now = datetime(2025, 4, 15, 10, 0, 0)
    assert is_match(settings, now) is False


def test_is_match_weekly_recurrence_with_occurrences_single_day():
    start = datetime(2025, 4, 7, 9, 0, 0)  # Monday
    end = datetime(2025, 4, 7, 17, 0, 0)  # Monday

    recurrence = Recurrence(
        {
            "Pattern": {
                "Type": "Weekly",
                "Interval": 2,
                "DaysOfWeek": ["Monday"],
                "FirstDayOfWeek": "Monday",
            },
            "Range": {"Type": "Numbered", "NumberOfOccurrences": 2},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    # First occurrence should match
    assert is_match(settings, datetime(2025, 4, 7, 10, 0, 0)) is True

    # Second week occurrence shouldn't match
    assert is_match(settings, datetime(2025, 4, 14, 10, 0, 0)) is False

    # Third week occurrence should match
    assert is_match(settings, datetime(2025, 4, 21, 10, 0, 0)) is True

    # Fourth week occurrence shouldn't match
    assert is_match(settings, datetime(2025, 4, 28, 10, 0, 0)) is False

    # Fifth week occurrence shouldn't match, passed the range
    assert is_match(settings, datetime(2025, 5, 5, 10, 0, 0)) is False


def test_is_match_weekly_recurrence_with_occurrences_multi_day():
    start = datetime(2025, 4, 7, 9, 0, 0)  # Monday
    end = datetime(2025, 4, 7, 17, 0, 0)  # Monday

    recurrence = Recurrence(
        {
            "Pattern": {
                "Type": "Weekly",
                "Interval": 2,
                "DaysOfWeek": ["Monday", "Tuesday"],
                "FirstDayOfWeek": "Monday",
            },
            "Range": {"Type": "Numbered", "NumberOfOccurrences": 4},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    # Before the start time, should not match
    assert is_match(settings, datetime(2025, 4, 7, 8, 0, 0)) is False  # Monday

    # First occurrence should match
    assert is_match(settings, datetime(2025, 4, 7, 10, 0, 0)) is True  # Monday
    assert is_match(settings, datetime(2025, 4, 8, 10, 0, 0)) is True  # Tuesday

    # Second week occurrence shouldn't match
    assert is_match(settings, datetime(2025, 4, 14, 10, 0, 0)) is False  # Monday
    assert is_match(settings, datetime(2025, 4, 15, 10, 0, 0)) is False  # Tuesday

    # Third week occurrence should match
    assert is_match(settings, datetime(2025, 4, 21, 10, 0, 0)) is True  # Monday
    assert is_match(settings, datetime(2025, 4, 22, 10, 0, 0)) is True  # Tuesday

    # Fourth week occurrence shouldn't match
    assert is_match(settings, datetime(2025, 4, 28, 10, 0, 0)) is False  # Monday
    assert is_match(settings, datetime(2025, 4, 29, 10, 0, 0)) is False  # Tuesday

    # Fifth week occurrence shouldn't match
    assert is_match(settings, datetime(2025, 5, 5, 10, 0, 0)) is False  # Monday
    assert is_match(settings, datetime(2025, 5, 6, 10, 0, 0)) is False  # Tuesday


def test_weekly_recurrence_start_after_min_offset():
    start = datetime(2025, 4, 9, 9, 0, 0)  # Monday
    end = datetime(2025, 4, 9, 17, 0, 0)  # Monday
    now = datetime(2025, 4, 12, 10, 0, 0)  # Saturday

    recurrence = Recurrence(
        {
            "Pattern": {
                "Type": "Weekly",
                "Interval": 1,
                "DaysOfWeek": ["Monday", "Wednesday"],
                "FirstDayOfWeek": "Monday",
            },
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    # Verify that the main method is_match correctly handles the scenario
    assert is_match(settings, now) is False
    assert is_match(settings, start) is True


def test_weekly_recurrence_now_before_min_offset():
    start = datetime(2025, 4, 9, 9, 0, 0)  # Monday
    end = datetime(2025, 4, 9, 17, 0, 0)  # Monday
    now = datetime(2025, 4, 16, 8, 0, 0)

    recurrence = Recurrence(
        {
            "Pattern": {
                "Type": "Weekly",
                "Interval": 1,
                "DaysOfWeek": ["Wednesday", "Friday"],
                "FirstDayOfWeek": "Monday",
            },
            "Range": {"Type": "NoEnd"},
        }
    )

    settings = TimeWindowFilterSettings(start=start, end=end, recurrence=recurrence)

    # Verify that the main method is_match correctly handles the scenario
    assert is_match(settings, now) is False
