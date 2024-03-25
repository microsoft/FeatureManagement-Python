# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from collections.abc import Mapping
from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._featurefilters import FeatureFilter
from ._models._feature_flag import FeatureFlag, _convert_boolean_value
import logging
import hashlib

FEATURE_MANAGEMENT_KEY = "feature_management"
FEATURE_FLAG_KEY = "feature_flags"

PROVIDED_FEATURE_FILTERS = "feature_filters"
FEATURE_FILTER_NAME = "name"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"

FEATURE_FILTER_PARAMETERS = "parameters"


def _get_feature_flag(configuration, feature_flag_name):
    feature_management = configuration.get(FEATURE_MANAGEMENT_KEY)
    if not feature_management or not isinstance(feature_management, Mapping):
        return None
    feature_flags = feature_management.get(FEATURE_FLAG_KEY)
    if not feature_flags or not isinstance(feature_flags, list):
        return None

    for feature_flag in feature_flags:
        if feature_flag.get("id") == feature_flag_name:
            return FeatureFlag.convert_from_json(feature_flag)

    return None


def _list_feature_flag_names(configuration):
    """
    List of all feature flag names
    """
    feature_flag_names = []
    feature_management = configuration.get(FEATURE_MANAGEMENT_KEY)
    if not feature_management or not isinstance(feature_management, Mapping):
        return []
    feature_flags = feature_management.get(FEATURE_FLAG_KEY)
    if not feature_flags or not isinstance(feature_flags, list):
        return []

    for feature_flag in feature_flags:
        feature_flag_names.append(feature_flag.get("id"))

    return feature_flag_names


class FeatureManager:
    """
    Feature Manager that determines if a feature flag is enabled for the given context

    :param configuration: Configuration object
    :type configuration: Mapping
    :keyword feature_filters: Custom filters to be used for evaluating feature flags
    :paramtype feature_filters: list[FeatureFilter]
    """

    def __init__(self, configuration, **kwargs):
        self._filters = {}
        if configuration is None or not isinstance(configuration, Mapping):
            raise AttributeError("Configuration must be a non-empty dictionary")
        self._configuration = configuration
        self._cache = {}
        self._copy = configuration.get(FEATURE_MANAGEMENT_KEY)
        filters = [TimeWindowFilter(), TargetingFilter()] + kwargs.pop(PROVIDED_FEATURE_FILTERS, [])

        for feature_filter in filters:
            if not isinstance(feature_filter, FeatureFilter):
                raise ValueError("Custom filter must be a subclass of FeatureFilter")
            self._filters[feature_filter.name] = feature_filter

    @staticmethod
    def _check_default_disabled_variant(feature_flag):
        if not feature_flag.allocation:
            return False
        return FeatureManager._check_variant_override(
            feature_flag.variants, feature_flag.allocation.default_when_disabled, False
        )

    @staticmethod
    def _check_default_enabled_variant(feature_flag):
        if not feature_flag.allocation:
            return True
        return FeatureManager._check_variant_override(
            feature_flag.variants, feature_flag.allocation.default_when_enabled, True
        )

    @staticmethod
    def _check_variant_override(variants, default_variant_name, status):
        if not variants or not default_variant_name:
            return status
        for variant in variants:
            if variant.name == default_variant_name:
                if variant.status_override == "Enabled":
                    return True
                elif variant.status_override == "Disabled":
                    return False
        return status

    @staticmethod
    def _is_targeted(context_id):
        """Determine if the user is targeted for the given context"""
        hashed_context_id = hashlib.sha256(context_id.encode()).hexdigest()
        context_marker = abs(int(hashed_context_id, 16))
        percentage = (context_marker / (2**256 - 1)) * 100

        return percentage

    def _assign_variant(self, feature_flag, **kwargs):
        if not feature_flag.variants or not feature_flag.allocation:
            return None
        if feature_flag.allocation.user:
            user = kwargs.get("user")
            if user:
                for user_allocation in feature_flag.allocation.user:
                    if user in user_allocation.users:
                        return user_allocation.variant
        if feature_flag.allocation.group:
            groups = kwargs.get("groups")
            if groups:
                for group_allocation in feature_flag.allocation.group:
                    for group in groups:
                        if group in group_allocation.groups:
                            return group_allocation.variant
        if feature_flag.allocation.percentile:
            user = kwargs.get("user", "")
            if user:
                context_id = user + "\n" + feature_flag.id + "\n" + feature_flag.allocation.seed
                box = self._is_targeted(context_id)
                for percentile_allocation in feature_flag.allocation.percentile:
                    if box == 100 and percentile_allocation.percentile_to == 100:
                        return percentile_allocation.variant
                    if percentile_allocation.percentile_from <= box < percentile_allocation.percentile_to:
                        return percentile_allocation.variant
        return None

    def is_enabled(self, feature_flag_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """
        if self._copy is not self._configuration.get(FEATURE_MANAGEMENT_KEY):
            self._cache = {}
            self._copy = self._configuration.get(FEATURE_MANAGEMENT_KEY)

        if not self._cache.get(feature_flag_id):
            feature_flag = _get_feature_flag(self._configuration, feature_flag_id)
            self._cache[feature_flag_id] = feature_flag
        else:
            feature_flag = self._cache.get(feature_flag_id)

        if not feature_flag:
            logging.warning("Feature flag %s not found", feature_flag_id)
            # Unknown feature flags are disabled by default
            return False

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            return FeatureManager._check_default_disabled_variant(feature_flag)

        feature_conditions = feature_flag.conditions
        feature_filters = feature_conditions.client_filters

        if len(feature_filters) == 0:
            # Feature flags without any filters return evaluate
            return FeatureManager._check_default_enabled_variant(feature_flag)

        result = False

        for feature_filter in feature_filters:
            filter_name = feature_filter[FEATURE_FILTER_NAME]
            if filter_name in self._filters:
                if feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL:
                    if not self._filters[filter_name].evaluate(feature_filter, **kwargs):
                        return False
                else:
                    if self._filters[filter_name].evaluate(feature_filter, **kwargs):
                        result = True
            else:
                raise ValueError(f"Feature flag {feature_flag_id} has unknown filter {filter_name}")
        if not feature_filters:
            # If this is reached, and true, default return value is true, else false
            result = feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL

        if feature_flag.allocation and feature_flag.variants:
            variant_name = self._assign_variant(feature_flag, **kwargs)
            if variant_name:
                return FeatureManager._check_variant_override(feature_flag.variants, variant_name, result)

        if result:
            return FeatureManager._check_default_enabled_variant(feature_flag)
        return FeatureManager._check_default_disabled_variant(feature_flag)
        # If this is reached, and true, default return value is true, else false
        return feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL

    def list_feature_flag_names(self):
        """
        List of all feature flag names
        """
        return _list_feature_flag_names(self._configuration)
