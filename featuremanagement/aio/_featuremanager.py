# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from collections.abc import Mapping
import logging
import hashlib
from typing import overload
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
from .._models import Variant, EvaluationEvent, TargetingContext


class FeatureManager:
    """
    Feature Manager that determines if a feature flag is enabled for the given context.

    :param Mapping configuration: Configuration object.
    :keyword list[FeatureFilter] feature_filters: Custom filters to be used for evaluating feature flags.
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
            return EvaluationEvent(enabled=False)
        return FeatureManager._check_variant_override(
            feature_flag.variants, feature_flag.allocation.default_when_disabled, False
        )

    @staticmethod
    def _check_default_enabled_variant(feature_flag):
        if not feature_flag.allocation:
            return EvaluationEvent(enabled=True)
        return FeatureManager._check_variant_override(
            feature_flag.variants, feature_flag.allocation.default_when_enabled, True
        )

    @staticmethod
    def _check_variant_override(variants, default_variant_name, status):
        if not variants or not default_variant_name:
            return EvaluationEvent(enabled=status)
        for variant in variants:
            if variant.name == default_variant_name:
                if variant.status_override == "Enabled":
                    return EvaluationEvent(enabled=True)
                if variant.status_override == "Disabled":
                    return EvaluationEvent(enabled=False)
        return EvaluationEvent(enabled=status)

    @staticmethod
    def _is_targeted(context_id):
        """Determine if the user is targeted for the given context"""
        hashed_context_id = hashlib.sha256(context_id.encode()).digest()
        context_marker = int.from_bytes(hashed_context_id[:4], byteorder="little", signed=False)

        return (context_marker / (2**32 - 1)) * 100

    def _assign_variant(self, feature_flag, targeting_context):
        if not feature_flag.variants or not feature_flag.allocation:
            return None
        if feature_flag.allocation.user and targeting_context.user_id:
            for user_allocation in feature_flag.allocation.user:
                if targeting_context.user_id in user_allocation.users:
                    return user_allocation.variant
        if feature_flag.allocation.group and len(targeting_context.groups) > 0:
            for group_allocation in feature_flag.allocation.group:
                for group in targeting_context.groups:
                    if group in group_allocation.groups:
                        return group_allocation.variant
        if feature_flag.allocation.percentile:
            context_id = targeting_context.user_id + "\n" + feature_flag.allocation.seed
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

    def _build_targeting_context(self, args):
        if len(args) == 1 and isinstance(args[0], str):
            return TargetingContext(user_id=args[0], groups=[])
        if len(args) == 1 and isinstance(args[0], TargetingContext):
            return args[0]
        return TargetingContext()

    @overload
    async def is_enabled(self, feature_flag_id, user_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """

    async def is_enabled(self, feature_flag_id, *args, **kwargs):
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """
        targeting_context = self._build_targeting_context(args)
        return (await self._check_feature(feature_flag_id, targeting_context, **kwargs)).enabled

    @overload
    async def get_variant(self, feature_flag_id, user_id, **kwargs):
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: return: Variant instance.
        :rtype: Variant
        """

    async def get_variant(self, feature_flag_id, *args, **kwargs):
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: Name of the variant.
        :rtype: str
        """
        targeting_context = self._build_targeting_context(args)
        result = await self._check_feature(feature_flag_id, targeting_context, **kwargs)
        return result.variant

    async def _check_feature_filters(self, feature_flag, targeting_context, **kwargs):
        feature_conditions = feature_flag.conditions
        feature_filters = feature_conditions.client_filters
        evaluation_event = EvaluationEvent(enabled=False)

        if len(feature_filters) == 0:
            # Feature flags without any filters return evaluate
            evaluation_event.enabled = True
        else:
            # The assumed value is no filters is based on the requirement type.
            # Requirement type Any assumes false until proven true, All assumes true until proven false
            evaluation_event.enabled = feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL

        for feature_filter in feature_filters:
            filter_name = feature_filter[FEATURE_FILTER_NAME]
            kwargs["user"] = targeting_context.user_id
            kwargs["groups"] = targeting_context.groups
            if filter_name not in self._filters:
                raise ValueError(f"Feature flag {feature_flag.name} has unknown filter {filter_name}")
            if feature_conditions.requirement_type == REQUIREMENT_TYPE_ALL:
                if not await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                    evaluation_event.enabled = False
                    break
            else:
                if await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                    evaluation_event.enabled = True
                    break
        return evaluation_event

    def _assign_allocation(self, feature_flag, evaluation_event, targeting_context, **kwargs):
        if feature_flag.allocation and feature_flag.variants:
            variant_name = self._assign_variant(feature_flag, targeting_context, **kwargs)
            if variant_name:
                evaluation_event = FeatureManager._check_variant_override(
                    feature_flag.variants, variant_name, evaluation_event.enabled
                )
                evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
                evaluation_event.feature = feature_flag
                return evaluation_event

        variant_name = None
        if evaluation_event.enabled:
            evaluation_event = FeatureManager._check_default_enabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_enabled
        else:
            evaluation_event = FeatureManager._check_default_disabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
        evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
        evaluation_event.feature = feature_flag
        return evaluation_event

    async def _check_feature(self, feature_flag_id, targeting_context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: True if the feature flag is enabled for the given context.
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
            return EvaluationEvent(enabled=False)

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            evaluation_event = FeatureManager._check_default_disabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
                evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
            evaluation_event.feature = feature_flag
            return evaluation_event

        evaluation_event = await self._check_feature_filters(feature_flag, targeting_context, **kwargs)

        return self._assign_allocation(feature_flag, evaluation_event, targeting_context, **kwargs)

    def list_feature_flag_names(self):
        """
        List of all feature flag names.
        """
        return _list_feature_flag_names(self._configuration)
