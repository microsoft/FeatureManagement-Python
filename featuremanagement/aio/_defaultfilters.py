# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from typing import Mapping, Any
from ._featurefilters import FeatureFilter
from .._defaultfilters import (
    TargetingFilter as SyncTargetingFilter,
    TimeWindowFilter as SyncTimeWindowFilter,
)


@FeatureFilter.alias("Microsoft.TimeWindow")
class TimeWindowFilter(FeatureFilter):
    """
    Feature Filter that determines if the current time is within the time window.
    """

    def __init__(self) -> None:
        self._filter = SyncTimeWindowFilter()

    async def evaluate(self, context: Mapping[Any, Any], **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :keyword Mapping context: Mapping with the Start and End time for the feature flag.
        :return: True if the current time is within the time window.
        :rtype: bool
        """
        return self._filter.evaluate(context, **kwargs)


@FeatureFilter.alias("Microsoft.Targeting")
class TargetingFilter(FeatureFilter):
    """
    Feature Filter that determines if the user is targeted for the feature flag.
    """

    def __init__(self) -> None:
        self._filter = SyncTargetingFilter()

    async def evaluate(self, context: Mapping[Any, Any], **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :keyword Mapping context: Context for evaluating the user/group.
        :return: True if the user is targeted for the feature flag.
        :rtype: bool
        """
        return self._filter.evaluate(context, **kwargs)
