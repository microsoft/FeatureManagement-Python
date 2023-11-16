# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import logging

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from ._featurefilters import FeatureFilter
from .._defaultfilters import (
    TargetingFilter as SyncTargetingFilter,
    TargetingException,
    FEATURE_FLAG_NAME_KEY,
    DEFAULT_ROLLOUT_PERCENTAGE_KEY,
    PARAMETERS_KEY,
    START_KEY,
    END_KEY,
    TARGETED_USER_KEY,
    TARGETED_GROUPS_KEY,
    AUDIENCE_KEY,
    USERS_KEY,
    GROUPS_KEY,
    EXCLUSION_KEY,
    FEATURE_FILTER_NAME_KEY,
    IGNORE_CASE_KEY,
)


@FeatureFilter.alias("Microsoft.TimeWindow")
class TimeWindowFilter(FeatureFilter):
    """
    Feature Filter that determines if the current time is within the time window
    """

    async def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :keyword Mapping context: Mapping with the Start and End time for the feature flag
        :paramtype context: Mapping
        :return: True if the current time is within the time window
        :rtype: bool
        """
        start = context.get(PARAMETERS_KEY, {}).get(START_KEY)
        end = context.get(PARAMETERS_KEY, {}).get(END_KEY)

        current_time = datetime.now(timezone.utc)

        if not start and not end:
            logging.warning("%s: At least one of Start or End is required.", TimeWindowFilter.__name__)
            return False

        start_time = parsedate_to_datetime(start) if start else None
        end_time = parsedate_to_datetime(end) if end else None

        return (start_time is None or start_time <= current_time) and (end_time is None or current_time < end_time)


@FeatureFilter.alias("Microsoft.Targeting")
class TargetingFilter(SyncTargetingFilter, FeatureFilter):
    """
    Feature Filter that determines if the user is targeted for the feature flag
    """

    async def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :keyword Mapping context: Context for evaluating the user/group
        :paramtype context: Mapping
        :return: True if the user is targeted for the feature flag
        :rtype: bool
        """
        target_user = kwargs.get(TARGETED_USER_KEY, None)
        target_groups = kwargs.get(TARGETED_GROUPS_KEY, [])

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
            if group.get(FEATURE_FILTER_NAME_KEY) in target_groups:
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

        # Check if the user is in the default rollout
        context_id = target_user + "\n" + feature_flag_name
        return self._is_targeted(context_id, default_rollout_percentage)
