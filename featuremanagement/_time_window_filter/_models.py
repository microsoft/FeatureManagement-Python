# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from enum import Enum
from typing import Dict, Any
from datetime import datetime
from dataclasses import dataclass
from email.utils import parsedate_to_datetime


class RecurrencePatternType(str, Enum):
    """
    The recurrence pattern type.
    """

    DAILY = "Daily"
    WEEKLY = "Weekly"

    @staticmethod
    def from_str(value: str) -> "RecurrencePatternType":
        """
        Get the RecurrencePatternType from the string value.

        :param value: The string value.
        :type value: str
        :return: The RecurrencePatternType.
        :rtype: RecurrencePatternType
        """
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

    @staticmethod
    def from_str(value: str) -> "RecurrenceRangeType":
        """
        Get the RecurrenceRangeType from the string value.

        :param value: The string value.
        :type value: str
        :return: The RecurrenceRangeType.
        :rtype: RecurrenceRangeType
        """
        if value == "NoEnd":
            return RecurrenceRangeType.NO_END
        if value == "EndDate":
            return RecurrenceRangeType.END_DATE
        if value == "Numbered":
            return RecurrenceRangeType.NUMBERED
        raise ValueError(f"Invalid value: {value}")


class RecurrencePattern:  # pylint: disable=too-few-public-methods
    """
    The recurrence pattern settings.
    """

    def __init__(self, pattern_data: Dict[str, Any]):
        self.type = RecurrencePatternType.from_str(pattern_data.get("Type", "Daily"))
        self.interval = pattern_data.get("Interval", 1)
        if self.interval <= 0:
            raise ValueError("The interval must be greater than 0.")
        self.days_of_week = pattern_data.get("DaysOfWeek", [])
        self.first_day_of_week = pattern_data.get("FirstDayOfWeek", 7)


class RecurrenceRange:  # pylint: disable=too-few-public-methods
    """
    The recurrence range settings.
    """

    def __init__(self, range_data: Dict[str, Any]):
        self.type = RecurrenceRangeType.from_str(range_data.get("Type", "NoEnd"))
        if range_data.get("EndDate") and isinstance(range_data.get("EndDate"), str):
            end_date_str = range_data.get("EndDate", "")
            self.end_date = parsedate_to_datetime(end_date_str) if end_date_str else None
        self.num_of_occurrences = range_data.get("NumberOfOccurrences", 0)
        if self.num_of_occurrences < 0:
            raise ValueError("The number of occurrences must be greater than or equal to 0.")


class Recurrence:  # pylint: disable=too-few-public-methods
    """
    The recurrence settings.
    """

    def __init__(self, recurrence_data: Dict[str, Any]):
        self.pattern = RecurrencePattern(recurrence_data.get("Pattern", {}))
        self.range = RecurrenceRange(recurrence_data.get("Range", {}))


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
