# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

from ._featurefilters import FeatureFilter
from .._defaultfilters import (
    TargetingFilter as SyncTargetingFilter,
    TimeWindowFilter as SyncTimeWindowFilter,
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
        time_window_filter = SyncTimeWindowFilter()
        return time_window_filter.evaluate(context, **kwargs)


@FeatureFilter.alias("Microsoft.Targeting")
class TargetingFilter(FeatureFilter):
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
        targeting_filter = SyncTargetingFilter()
        return targeting_filter.evaluate(context, **kwargs)
