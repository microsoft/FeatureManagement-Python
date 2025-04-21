# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import logging
import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import cast, List, Mapping, Optional, Dict, Any
from ._featurefilters import FeatureFilter
from ._time_window_filter import Recurrence, is_match, TimeWindowFilterSettings

FEATURE_FLAG_NAME_KEY = "feature_name"
ROLLOUT_PERCENTAGE_KEY = "RolloutPercentage"
DEFAULT_ROLLOUT_PERCENTAGE_KEY = "DefaultRolloutPercentage"
PARAMETERS_KEY = "parameters"

# Time Window Constants
START_KEY = "Start"
END_KEY = "End"
TIME_WINDOW_FILTER_SETTING_RECURRENCE = "Recurrence"

# Time Window Exceptions
TIME_WINDOW_FILTER_INVALID = (
    "{}: The {} feature filter is not valid for feature {}. It must specify either {}, {}, or both."
)
TIME_WINDOW_FILTER_INVALID_RECURRENCE = (
    "{}: The {} feature filter is not valid for feature {}. It must specify both {} and {} when Recurrence is not None."
)

# Targeting kwargs
TARGETED_USER_KEY = "user"
TARGETED_GROUPS_KEY = "groups"

# Targeting Constants
AUDIENCE_KEY = "Audience"
USERS_KEY = "Users"
GROUPS_KEY = "Groups"
EXCLUSION_KEY = "Exclusion"
FEATURE_FILTER_NAME_KEY = "Name"
IGNORE_CASE_KEY = "ignore_case"

logger = logging.getLogger(__name__)


class TargetingException(Exception):
    """
    Exception raised when the targeting filter is not configured correctly.
    """


@FeatureFilter.alias("Microsoft.TimeWindow")
class TimeWindowFilter(FeatureFilter):
    """
    Feature Filter that determines if the current time is within the time window.
    """

    def evaluate(self, context: Mapping[Any, Any], **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :keyword Mapping context: Mapping with the Start and End time for the feature flag.
        :return: True if the current time is within the time window.
        :rtype: bool
        """
        start = context.get(PARAMETERS_KEY, {}).get(START_KEY, None)
        end = context.get(PARAMETERS_KEY, {}).get(END_KEY, None)
        recurrence_data = context.get(PARAMETERS_KEY, {}).get(TIME_WINDOW_FILTER_SETTING_RECURRENCE, None)
        recurrence = None

        current_time = datetime.now(timezone.utc)

        if not start and not end:
            logger.warning(
                TIME_WINDOW_FILTER_INVALID,
                TimeWindowFilter.__name__,
                context.get(FEATURE_FLAG_NAME_KEY),
                START_KEY,
                END_KEY,
            )
            return False

        start_time: Optional[datetime] = parsedate_to_datetime(start) if start else None
        end_time: Optional[datetime] = parsedate_to_datetime(end) if end else None

        if (start_time is None or start_time <= current_time) and (end_time is None or current_time < end_time):
            return True

        if recurrence_data:
            recurrence = Recurrence(recurrence_data)
            settings = TimeWindowFilterSettings(start_time, end_time, recurrence)
            return is_match(settings, current_time)

        return False


@FeatureFilter.alias("Microsoft.Targeting")
class TargetingFilter(FeatureFilter):
    """
    Feature Filter that determines if the user is targeted for the feature flag.
    """

    @staticmethod
    def _is_targeted(context_id: str, rollout_percentage: int) -> bool:
        """Determine if the user is targeted for the given context"""
        # Always return true if rollout percentage is 100
        if rollout_percentage == 100:
            return True

        hashed_context_id = hashlib.sha256(context_id.encode()).digest()
        context_marker = int.from_bytes(hashed_context_id[:4], byteorder="little", signed=False)

        percentage = (context_marker / (2**32 - 1)) * 100
        return percentage < rollout_percentage

    def _target_group(
        self, target_user: Optional[str], target_group: str, group: Mapping[str, Any], feature_flag_name: str
    ) -> bool:
        group_rollout_percentage = group.get(ROLLOUT_PERCENTAGE_KEY, 0)
        if not target_user:
            target_user = ""
        audience_context_id = target_user + "\n" + feature_flag_name + "\n" + target_group

        return self._is_targeted(audience_context_id, group_rollout_percentage)

    def evaluate(self, context: Mapping[Any, Any], **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :keyword Mapping context: Context for evaluating the user/group.
        :return: True if the user is targeted for the feature flag.
        :rtype: bool
        """
        target_user: Optional[str] = cast(
            str,
            kwargs.get(TARGETED_USER_KEY, None),
        )
        target_groups: List[str] = cast(List[str], kwargs.get(TARGETED_GROUPS_KEY, []))

        if not target_user and not (target_groups and len(target_groups) > 0):
            logging.warning("%s: Name or Groups are required parameters", TargetingFilter.__name__)
            return False

        audience = context.get(PARAMETERS_KEY, {}).get(AUDIENCE_KEY, None)
        feature_flag_name = context.get(FEATURE_FLAG_NAME_KEY, None)

        if not audience:
            raise TargetingException("Audience is required for " + TargetingFilter.__name__)

        groups = audience.get(GROUPS_KEY, [])
        default_rollout_percentage = audience.get(DEFAULT_ROLLOUT_PERCENTAGE_KEY, 0)

        self._validate(groups, default_rollout_percentage)

        # Check if the user is excluded
        if target_user in audience.get(EXCLUSION_KEY, {}).get(USERS_KEY, []):
            return False

        # Check if the user is in an excluded group
        for group in audience.get(EXCLUSION_KEY, {}).get(GROUPS_KEY, []):
            if group in target_groups:
                return False

        # Check if the user is targeted
        if target_user in audience.get(USERS_KEY, []):
            return True

        # Check if the user is in a targeted group
        for group in groups:
            for target_group in target_groups:
                group_name = group.get(FEATURE_FILTER_NAME_KEY, "")
                if kwargs.get(IGNORE_CASE_KEY, False):
                    target_group = target_group.lower()
                    group_name = group_name.lower()
                if group_name == target_group:
                    if self._target_group(target_user, target_group, group, feature_flag_name):
                        return True

        if not target_user:
            target_user = ""
        # Check if the user is in the default rollout
        context_id = target_user + "\n" + feature_flag_name
        return self._is_targeted(context_id, default_rollout_percentage)

    @staticmethod
    def _validate(groups: List[Dict[str, Any]], default_rollout_percentage: int) -> None:
        # Validate the audience settings
        if default_rollout_percentage < 0 or default_rollout_percentage > 100:
            raise TargetingException("DefaultRolloutPercentage must be between 0 and 100")

        for group in groups:
            if group.get(ROLLOUT_PERCENTAGE_KEY, 0) < 0 or group.get(ROLLOUT_PERCENTAGE_KEY, 100) > 100:
                raise TargetingException("RolloutPercentage must be between 0 and 100")
