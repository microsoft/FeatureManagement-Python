import pytest
from datetime import datetime, timedelta
from featuremanagement._time_window_filter._models import Recurrence
from featuremanagement._time_window_filter._recurrence_validator import validate_settings

def valid_daily_pattern():
    return {
        "Type": "Daily",
        "Interval": 1,
        "DaysOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "FirstDayOfWeek": "Sunday",
    }

def valid_daily_recurrence():
    return Recurrence(
        {
            "Pattern": valid_daily_pattern(),
            "Range": {"Type": "NoEnd", "EndDate": None, "NumberOfOccurrences": 10},
        }
    )

def valid_daily_end_date_recurrence():
    return Recurrence(
        {
            "Pattern": valid_daily_pattern(),
            "Range": {"Type": "EndDate", "EndDate": datetime.now() + timedelta(days=10), "NumberOfOccurrences": 10},
        }
    )

def valid_weekly_recurrence():
    return Recurrence(
        {
            "Pattern": {
                "Type": "Weekly",
                "Interval": 1,
                "DaysOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "FirstDayOfWeek": "Monday",
            },
            "Range": {"Type": "NoEnd", "EndDate": None, "NumberOfOccurrences": 10},
        }
    )


def test_validate_settings_valid_daily():
    start = datetime.now()
    end = start + timedelta(days=1)
    validate_settings(valid_daily_recurrence(), start, end)

def test_validate_settings_valid_daily_end_date():
    start = datetime.now()
    end = start + timedelta(days=1)
    validate_settings(valid_daily_end_date_recurrence(), start, end)


def test_validate_settings_valid_weekly():
    start = datetime.now()
    end = start + timedelta(days=1)
    validate_settings(valid_weekly_recurrence(), start, end)

def test_validate_settings_duration_exceeds_ten_years():
    start = datetime.now()
    end = start + timedelta(days=3651)
    with pytest.raises(ValueError, match="Time window duration exceeds ten years: end"):
        validate_settings(valid_daily_recurrence(), start, end)

def test_validate_settings_invalid_start_end():
    start = datetime.now() + timedelta(days=1)
    end = datetime.now()
    with pytest.raises(ValueError, match="The filter start date Start needs to before the End date."):
        validate_settings(valid_daily_recurrence(), start, end)

def test_validate_settings_end_date_in_past():
    start = datetime.now()
    end = datetime.now() - timedelta(days=1)
    with pytest.raises(ValueError, match="The filter start date Start needs to before the End date."):
        validate_settings(valid_daily_recurrence(), start, end)

def test_validate_settings_missing_recurrence():
    start = datetime.now()
    end = start + timedelta(days=1)
    with pytest.raises(ValueError, match="Recurrence is required"):
        validate_settings(None, start, end)

def test_validate_settings_invalid_recurrence_pattern():
    with pytest.raises(ValueError, match="Invalid value: InvalidType"):
         Recurrence({"Pattern": {"Type": "InvalidType"}, "Range": {"Type": "NoEnd"}})


