# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from datetime import timedelta, datetime
import pytest
from recurrence_util import valid_daily_recurrence, valid_daily_end_date_recurrence, valid_no_end_range, START, END
from featuremanagement._time_window_filter._models import Recurrence
from featuremanagement._time_window_filter._recurrence_validator import validate_settings


def test_validate_settings_valid_daily():
    validate_settings(valid_daily_recurrence(), START, END)


def test_validate_settings_valid_daily_end_date():
    validate_settings(valid_daily_end_date_recurrence(), START, END)


def test_validate_settings_valid_weekly_one_day():
    validate_settings(
        Recurrence(
            {
                "Pattern": {
                    "Type": "Weekly",
                    "Interval": 1,
                    "DaysOfWeek": ["Monday"],
                    "FirstDayOfWeek": "Monday",
                },
                "Range": valid_no_end_range(),
            }
        ),
        START,
        END,
    )


def test_validate_settings_valid_weekly():
    validate_settings(
        Recurrence(
            {
                "Pattern": {
                    "Type": "Weekly",
                    "Interval": 1,
                    "DaysOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "FirstDayOfWeek": "Monday",
                },
                "Range": valid_no_end_range(),
            }
        ),
        START,
        END,
    )


def test_validate_settings_duration_exceeds_ten_years():
    end = START + timedelta(days=3651)
    with pytest.raises(ValueError, match="Time window duration exceeds ten years: end"):
        validate_settings(valid_daily_recurrence(), START, end)


def test_validate_settings_invalid_start_end():
    start = START + timedelta(days=2)
    with pytest.raises(ValueError, match="The filter start date Start needs to before the End date."):
        validate_settings(valid_daily_recurrence(), start, END)


def test_validate_settings_end_date_in_past():
    end = START - timedelta(days=1)
    with pytest.raises(ValueError, match="The filter start date Start needs to before the End date."):
        validate_settings(valid_daily_recurrence(), START, end)


def test_validate_settings_missing_recurrence():
    with pytest.raises(ValueError, match="Recurrence is required"):
        validate_settings(None, START, END)


def test_validate_settings_invalid_recurrence_pattern():
    with pytest.raises(ValueError, match="Invalid value: InvalidType"):
        Recurrence({"Pattern": {"Type": "InvalidType"}, "Range": {"Type": "NoEnd"}})


def test_validate_settings_weekly_recurrence_invalid_start_day():
    with pytest.raises(ValueError, match="Start day does not match any day of the week: Monday"):
        validate_settings(
            Recurrence(
                {
                    "Pattern": {
                        "Type": "Weekly",
                        "Interval": 1,
                        "DaysOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday"],
                        "FirstDayOfWeek": "Monday",
                    },
                    "Range": valid_no_end_range(),
                }
            ),
            START,
            END,
        )


def test_validate_settings_period_too_long():
    end = START + timedelta(days=7)
    with pytest.raises(ValueError, match="Time window duration is out of range:"):
        validate_settings(valid_daily_recurrence(), START, end)


def test_validate_settings_no_days_of_week():
    with pytest.raises(ValueError, match="Required parameter: Recurrence.Pattern.DaysOfWeek"):
        validate_settings(
            Recurrence(
                {
                    "Pattern": {
                        "Type": "Weekly",
                        "Interval": 1,
                        "FirstDayOfWeek": "Monday",
                    },
                    "Range": valid_no_end_range(),
                }
            ),
            START,
            END,
        )


def test_validate_settings_end_date_before_start():
    with pytest.raises(ValueError, match="The Recurrence.Range.EndDate should be after the Start"):
        validate_settings(valid_daily_end_date_recurrence(), START + timedelta(days=11), END + timedelta(days=11))


def test_is_duration_compliant_with_days_of_week_false():
    pattern = {
        "Type": "Weekly",
        "Interval": 1,
        "DaysOfWeek": ["Monday", "Wednesday"],
        "FirstDayOfWeek": "Monday",
    }

    start = datetime(2025, 4, 7, 9, 0, 0)  # Monday
    end = datetime(2025, 4, 10, 9, 0, 0)  # Wednesday (48 hours duration)
    with pytest.raises(ValueError, match="Recurrence.Pattern.DaysOfWeek"):
        validate_settings(Recurrence({"Pattern": pattern, "Range": valid_no_end_range()}), start, end)
