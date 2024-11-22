# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from enum import Enum
from datetime import datetime
from typing import List
from dataclasses import dataclass


class RecurrencePatternType(str, Enum):
    """
    The recurrence pattern type.
    """

    DAILY = "Daily"
    WEEKLY = "Weekly"


class RecurrenceRangeType(str, Enum):
    """
    The recurrence range type.
    """

    NO_END = "NoEnd"
    END_DATE = "EndDate"
    NUMBERED = "Numbered"


@dataclass
class RecurrencePattern:
    """
    The recurrence pattern settings.
    """

    days_of_week: List[int]
    interval: int = 1
    first_day_of_week: int = 7
    type: RecurrencePatternType = RecurrencePatternType.DAILY


@dataclass
class RecurrenceRange:
    """
    The recurrence range settings.
    """

    end_date: datetime
    num_of_occurrences: int
    type: RecurrenceRangeType = RecurrenceRangeType.NO_END


@dataclass
class Recurrence:
    """
    The recurrence settings.
    """

    pattern: RecurrencePattern
    range: RecurrenceRange


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
