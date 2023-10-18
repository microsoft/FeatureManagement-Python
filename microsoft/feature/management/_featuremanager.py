# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

from ._defaultfilters import TimeWindowFilter, TargetingFilter

FEATURE_MANAGEMENT_KEY = "FeatureManagement"
FEATURE_FLAGS_SECTION = "FeatureFlags"

TIME_WINDOW_FILTER_NAME = "Microsoft.TimeWindowFilter"
TARGETING_FILTER_NAME = "Microsoft.Targeting"

PROVIDED_FEATURE_FILTERS = "feature_filters"

FEATURE_FLAG_ID = "id"
FEATURE_FLAG_ENABLED = "enabled"
FEATURE_FLAG_CONDITIONS = "conditions"
FEATURE_FLAG_CLIENT_FILTERS = "client_filters"
FEATURE_FILTER_NAME = "name"
FEATURE_FILTER_REQUIREMENT_TYPE = "requirement_type"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"
FEATURE_FILTER_PARAMETERS = "parameters"


class FeatureManager:
    """
    Feature Manager that determines if a feature flag is enabled for the given context
    """

    def __init__(self, feature_flags, **kwargs):
        feature_flags = feature_flags.get(FEATURE_MANAGEMENT_KEY, feature_flags)
        feature_flags_list = feature_flags.get(FEATURE_FLAGS_SECTION, feature_flags)
        self._feature_flags = {}
        for feature_flag in feature_flags_list:
            self._validate_feature_flag(feature_flag)
            self._feature_flags[feature_flag[FEATURE_FLAG_ID]] = feature_flag

        feature_filters = {}
        feature_filters[TIME_WINDOW_FILTER_NAME] = TimeWindowFilter()
        feature_filters[TARGETING_FILTER_NAME] = TargetingFilter()
        feature_filters.update(kwargs.pop(PROVIDED_FEATURE_FILTERS, {}))
        self._filters = feature_filters

    @staticmethod
    def _validate_feature_flag(feature_flag):
        if feature_flag.get(FEATURE_FLAG_ID, None) is None:
            raise ValueError("Feature flag id field is required")
        if feature_flag.get(FEATURE_FLAG_ENABLED, None) is None:
            raise ValueError("Feature flag enabled field is required")
        if feature_flag.get(FEATURE_FLAG_CONDITIONS, None) is not None:
            if feature_flag[FEATURE_FLAG_CONDITIONS].get(FEATURE_FLAG_CLIENT_FILTERS, None) is not None:
                for feature_filter in feature_flag[FEATURE_FLAG_CONDITIONS][FEATURE_FLAG_CLIENT_FILTERS]:
                    if feature_filter.get(FEATURE_FILTER_NAME, None) is None:
                        raise ValueError("Feature flag filter name field is required")

    def is_enabled(self, feature_flag_name, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_name: Name of the feature flag
        :paramtype feature_flag_name: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """
        feature_flag = self._feature_flags.get(feature_flag_name, None)

        if not feature_flag:
            print("Feature flag not found")
            # Unknown feature flags are disabled by default
            return False

        if not _check_is_true(feature_flag[FEATURE_FLAG_ENABLED]):
            # Feature flags that are disabled are always disabled
            return False

        if (
            len(
                feature_flag.get(FEATURE_FLAG_CONDITIONS, {FEATURE_FLAG_CLIENT_FILTERS: []})[
                    FEATURE_FLAG_CLIENT_FILTERS
                ]
            )
            == 0
        ):
            # Feature flags without any filters return evaluate
            return True

        for feature_filter in feature_flag[FEATURE_FLAG_CONDITIONS][FEATURE_FLAG_CLIENT_FILTERS]:
            filter_name = feature_filter[FEATURE_FILTER_NAME]
            if filter_name in self._filters:
                if feature_flag.get(FEATURE_FILTER_REQUIREMENT_TYPE, REQUIREMENT_TYPE_ANY) == REQUIREMENT_TYPE_ALL:
                    if not self._filters[filter_name].evaluate(feature_filter[FEATURE_FILTER_PARAMETERS], **kwargs):
                        return False
                else:
                    if self._filters[filter_name].evaluate(feature_filter, **kwargs):
                        return True
        # If this is reached, and true, default return value is true, else false
        return feature_flag.get(FEATURE_FILTER_REQUIREMENT_TYPE, REQUIREMENT_TYPE_ANY) == REQUIREMENT_TYPE_ALL

    def list_feature_flag_names(self):
        """
        List of all feature flag names
        """
        return self._feature_flags.keys()


def _check_is_true(enabled):
    if enabled.lower() == "true":
        return True
    if enabled.lower() == "false":
        return False
    return enabled
