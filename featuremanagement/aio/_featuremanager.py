# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from collections.abc import Mapping
import logging
import hashlib
from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._featurefilters import FeatureFilter
from .._featuremanager import (
    PROVIDED_FEATURE_FILTERS,
    FEATURE_FILTER_NAME,
    REQUIREMENT_TYPE_ALL,
    FEATURE_MANAGEMENT_KEY,
    _get_feature_flag,
    _list_feature_flag_names,
)
from .._models._variant import Variant


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
                if variant.status_override == "Disabled":
                    return False
        return status

    @staticmethod
    def _is_targeted(context_id):
        """Determine if the user is targeted for the given context"""
        hashed_context_id = hashlib.sha256(context_id.encode()).digest()
        context_marker = int.from_bytes(hashed_context_id[:4], byteorder="little", signed=False)

        return (context_marker / (2**32 - 1)) * 100

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
            context_id = user + "\n" + feature_flag.allocation.seed
            box = self._is_targeted(context_id)
            for percentile_allocation in feature_flag.allocation.percentile:
                if box == 100 and percentile_allocation.percentile_to == 100:
                    return percentile_allocation.variant
                if percentile_allocation.percentile_from <= box < percentile_allocation.percentile_to:
                    return percentile_allocation.variant
        return None

    def _variant_name_to_variant(self, feature_flag, variant_name):
        if not feature_flag.variants:
            return None
        for variant_reference in feature_flag.variants:
            if variant_reference.name == variant_name:
                configuration = variant_reference.configuration_value
                if not configuration:
                    configuration = self._configuration.get(variant_reference.configuration_reference)
                return Variant(variant_reference.name, configuration)
        return None

    async def is_enabled(self, feature_flag_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """
        return (await self._check_feature(feature_flag_id, **kwargs))["enabled"]

    async def get_variant(self, feature_flag_id, **kwargs):
        """
        Determine the variant for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: Name of the variant
        :rtype: str
        """
        return (await self._check_feature(feature_flag_id, **kwargs))["variant"]

    async def _check_feature(self, feature_flag_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """
        result = {"enabled": None, "variant": None}
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
            return result

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            result["enabled"] = FeatureManager._check_default_disabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
                result["variant"] = self._variant_name_to_variant(feature_flag, variant_name)
            return result

        feature_conditions = feature_flag.conditions
        feature_filters = feature_conditions.client_filters

        if len(feature_filters) == 0:
            # Feature flags without any filters return evaluate
            result["enabled"] = True
        else:
            # The assumed value is no filters is based on the requirement type.
            # Requirement type Any assumes false until proven true, All assumes true until proven false
            result["enabled"] = feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL

        for feature_filter in feature_filters:
            filter_name = feature_filter[FEATURE_FILTER_NAME]
            if filter_name not in self._filters:
                raise ValueError(f"Feature flag {feature_flag_id} has unknown filter {filter_name}")
            if feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL:
                if not await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                    result["enabled"] = False
                    break
            else:
                if await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                    result["enabled"] = True
                    break

        if feature_flag.allocation and feature_flag.variants:
            variant_name = self._assign_variant(feature_flag, **kwargs)
            if variant_name:
                result["enabled"] = FeatureManager._check_variant_override(
                    feature_flag.variants, variant_name, result["enabled"]
                )
                result["variant"] = self._variant_name_to_variant(feature_flag, variant_name)
                return result

        variant_name = None
        if result["enabled"]:
            result["enabled"] = FeatureManager._check_default_enabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_enabled
        else:
            result["enabled"] = FeatureManager._check_default_disabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
        result["variant"] = self._variant_name_to_variant(feature_flag, variant_name)
        return result

    def list_feature_flag_names(self):
        """
        List of all feature flag names
        """
        return _list_feature_flag_names(self._configuration)
