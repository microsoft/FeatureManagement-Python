from datetime import datetime, timedelta
from featuremanagement._time_window_filter._models import Recurrence

DATE_FORMAT = "%a, %d %b %Y %H:%M:%S"

START_STRING = "Mon, 31 Mar 2025 00:00:00"
START = datetime.strptime(START_STRING, DATE_FORMAT)
END_STRING = "Mon, 31 Mar 2025 23:59:59"
END = datetime.strptime(END_STRING, DATE_FORMAT)


def valid_daily_pattern():
    return {
        "Type": "Daily",
        "Interval": 1,
        "DaysOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "FirstDayOfWeek": "Sunday",
    }


def valid_no_end_range():
    return {
        "Type": "NoEnd",
        "EndDate": None,
        "NumberOfOccurrences": 10,
    }


def valid_daily_recurrence():
    return Recurrence(
        {
            "Pattern": valid_daily_pattern(),
            "Range": valid_no_end_range(),
        }
    )


def valid_daily_end_date_recurrence():
    return Recurrence(
        {
            "Pattern": valid_daily_pattern(),
            "Range": {
                "Type": "EndDate",
                "EndDate": (START + timedelta(days=10)).strftime(DATE_FORMAT),
                "NumberOfOccurrences": 10,
            },
        }
    )
