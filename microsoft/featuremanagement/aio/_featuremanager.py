# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._featurefilters import FeatureFilter
from .._featuremanager import (
    FeatureManager as SyncFeatureManager,
    PROVIDED_FEATURE_FILTERS,
    FEATURE_FILTER_NAME,
    REQUIREMENT_TYPE_ALL,
    FEATURE_FILTER_PARAMETERS,
)
import logging


class FeatureManager(SyncFeatureManager):
    """
    Feature Manager that determines if a feature flag is enabled for the given context
    """

    def __init__(self, configuration, **kwargs):
        self._filters = {}
        self._configuration = configuraiton

        filters = [TimeWindowFilter(), TargetingFilter()] + kwargs.pop(PROVIDED_FEATURE_FILTERS, [])

        for filter in filters:
            if not isinstance(filter, FeatureFilter):
                raise ValueError("Custom filter must be a subclass of FeatureFilter")
            self._filters[filter.name] = filter

    async def is_enabled(self, feature_flag_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """
        feature_flag = self._get_feature_flag(feature_flag_id)

        if not feature_flag:
            logging.warning("Feature flag {} not found".format(feature_flag_id))
            # Unknown feature flags are disabled by default
            return False

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            return False

        feature_conditions = feature_flag.conditions
        feature_filters = feature_conditions.client_filters

        if len(feature_filters) == 0:
            # Feature flags without any filters return evaluate
            return True

        for feature_filter in feature_filters:
            filter_name = feature_filter[FEATURE_FILTER_NAME]
            if filter_name in self._filters:
                if feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL:
                    if not await self._filters[filter_name].evaluate(
                        feature_filter[FEATURE_FILTER_PARAMETERS], **kwargs
                    ):
                        return False
                else:
                    if await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                        return True
        # If this is reached, and true, default return value is true, else false
        return feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL
