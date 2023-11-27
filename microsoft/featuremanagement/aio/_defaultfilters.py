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
    TimeWindowFilter as SyncTimeWindowFilter,
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
class TimeWindowFilter(SyncTimeWindowFilter, FeatureFilter):
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
        return super().evaluate(context, **kwargs)


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
        return super().evaluate(context, **kwargs)
