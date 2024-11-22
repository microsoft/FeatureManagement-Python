# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from enum import Enum
from datetime import datetime
from typing import Self
from dataclasses import dataclass
from email.utils import parsedate_to_datetime


class RecurrencePatternType(str, Enum):
    """
    The recurrence pattern type.
    """

    DAILY = "Daily"
    WEEKLY = "Weekly"

    def from_str(value: str) -> Self:
        if value == "Daily":
            return RecurrencePatternType.DAILY
        if value == "Weekly":
            return RecurrencePatternType.WEEKLY
        raise ValueError(f"Invalid value: {value}")


class RecurrenceRangeType(str, Enum):
    """
    The recurrence range type.
    """

    NO_END = "NoEnd"
    END_DATE = "EndDate"
    NUMBERED = "Numbered"

    def from_str(value: str) -> Self:
        if value == "NoEnd":
            return RecurrenceRangeType.NO_END
        if value == "EndDate":
            return RecurrenceRangeType.END_DATE
        if value == "Numbered":
            return RecurrenceRangeType.NUMBERED
        raise ValueError(f"Invalid value: {value}")

class RecurrencePattern:
    """
    The recurrence pattern settings.
    """

    def __init__(self, pattern_data: dict[str: any]):
        self.type = RecurrencePatternType.from_str(pattern_data.get("Type", "Daily"))
        self.interval = pattern_data.get("Interval", 1)
        self.days_of_week = pattern_data.get("DaysOfWeek", [])
        self.first_day_of_week = pattern_data.get("FirstDayOfWeek", 7)

class RecurrenceRange:
    """
    The recurrence range settings.
    """

    def __init__(self, range_data: dict[str: any]):
        self.type = RecurrenceRangeType.from_str(range_data.get("Type", "NoEnd"))
        if range_data.get("EndDate"):
            self.end_date = parsedate_to_datetime(range_data.get("EndDate"))
        self.num_of_occurrences = range_data.get("NumberOfOccurrences")

class Recurrence:
    """
    The recurrence settings.
    """

    def __init__(self, recurrence_data: dict[str: any]):
        self.pattern = RecurrencePattern(recurrence_data.get("Pattern"))
        self.range = RecurrenceRange(recurrence_data.get("Range"))


@dataclass
class TimeWindowFilterSettings:
    """
    The settings for the time window filter.
    """

    start: datetime
    end: datetime
    recurrence: Recurrence


@dataclass
class OccurrenceInfo:
    """
    The information of the previous occurrence.
    """

    previous_occurrence: datetime
    num_of_occurrences: int
