# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from collections.abc import Mapping
import logging
import hashlib
import inspect
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
from .._models import Variant, EvaluationEvent, VariantAssignmentReason, TargetingContext


class FeatureManager:
    """
    Feature Manager that determines if a feature flag is enabled for the given context.

    :param Mapping configuration: Configuration object.
    :keyword list[FeatureFilter] feature_filters: Custom filters to be used for evaluating feature flags.
    :keyword Callable[EvaluationEvent] on_feature_evaluated: Callback function to be called when a feature flag is
    evaluated.
    """

    def __init__(self, configuration, **kwargs):
        self._filters = {}
        if configuration is None or not isinstance(configuration, Mapping):
            raise AttributeError("Configuration must be a non-empty dictionary")
        self._configuration = configuration
        self._cache = {}
        self._copy = configuration.get(FEATURE_MANAGEMENT_KEY)
        self._on_feature_evaluated = kwargs.pop("on_feature_evaluated", None)
        filters = [TimeWindowFilter(), TargetingFilter()] + kwargs.pop(PROVIDED_FEATURE_FILTERS, [])

        for feature_filter in filters:
            if not isinstance(feature_filter, FeatureFilter):
                raise ValueError("Custom filter must be a subclass of FeatureFilter")
            self._filters[feature_filter.name] = feature_filter

    @staticmethod
    def _check_default_disabled_variant(feature_flag):
        """
        A method called when the feature flag is disabled, to determine what the default variant should be. If there is
        no allocation, then None is set as the value of the variant in the EvaluationEvent.

        :param FeatureFlag feature_flag: Feature flag object.
        :return: EvaluationEvent
        """
        if not feature_flag.allocation:
            return EvaluationEvent(enabled=False)
        return FeatureManager._check_variant_override(
            feature_flag.variants, feature_flag.allocation.default_when_disabled, False
        )

    @staticmethod
    def _check_default_enabled_variant(feature_flag):
        """
        A method called when the feature flag is enabled, to determine what the default variant should be. If there is
        no allocation, then None is set as the value of the variant in the EvaluationEvent.

        :param FeatureFlag feature_flag: Feature flag object.
        :return: EvaluationEvent
        """
        if not feature_flag.allocation:
            return EvaluationEvent(enabled=True)
        return FeatureManager._check_variant_override(
            feature_flag.variants, feature_flag.allocation.default_when_enabled, True
        )

    @staticmethod
    def _check_variant_override(variants, default_variant_name, status):
        """
        A method to check if a variant is overridden to be enabled or disabled by the variant.

        :param list[Variant] variants: List of variants.
        :param str default_variant_name: Name of the default variant.
        :param bool status: Status of the feature flag.
        :return: EvaluationEvent
        """
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

    def _assign_variant(self, feature_flag, **kwargs):
        """
        Assign a variant to the user based on the allocation.
        :param FeatureFlag feature_flag: Feature flag object.
        :param TargetingContext targeting_context: Targeting context.
        :return: Variant name.
        """
        user = kwargs.get("user", "")
        groups = kwargs.get("groups", [])
        evaluation_event = EvaluationEvent(feature_flag=feature_flag)
        if not feature_flag.variants or not feature_flag.allocation:
            return None
        if feature_flag.allocation.user and user:
            for user_allocation in feature_flag.allocation.user:
                if user in user_allocation.users:
                    evaluation_event.reason = VariantAssignmentReason.USER
                    return user_allocation.variant, evaluation_event
        if feature_flag.allocation.group and groups:
            for group_allocation in feature_flag.allocation.group:
                for group in groups:
                    if group in group_allocation.groups:
                        evaluation_event.reason = VariantAssignmentReason.GROUP
                        return group_allocation.variant, evaluation_event
        if feature_flag.allocation.percentile:
            context_id = targeting_context.user_id + "\n" + feature_flag.allocation.seed
            box = self._is_targeted(context_id)
            for percentile_allocation in feature_flag.allocation.percentile:
                if box == 100 and percentile_allocation.percentile_to == 100:
                    return percentile_allocation.variant
                if percentile_allocation.percentile_from <= box < percentile_allocation.percentile_to:
                    evaluation_event.reason = VariantAssignmentReason.PERCENTILE
                    return percentile_allocation.variant, evaluation_event
        return None, evaluation_event

    def _variant_name_to_variant(self, feature_flag, variant_name):
        """
        Get the variant object from the variant name.

        :param FeatureFlag feature_flag: Feature flag object.
        :param str variant_name: Name of the variant.
        :return: Variant object.
        """
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
        """
        Builds a TargetingContext, either returns a provided context, takes the provided user_id to make a context, or
        returns an empty context.
        
        :param args: Arguments to build the TargetingContext.
        :return: TargetingContext
        """
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

        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """
        result = await self._check_feature(feature_flag_id, **kwargs)
        if self._on_feature_evaluated and result.feature.telemetry.enabled:
            result.user = kwargs.get("user", "")
            if inspect.iscoroutinefunction(self._on_feature_evaluated):
                await self._on_feature_evaluated(result)
            else:
                self._on_feature_evaluated(result)
        return result.variant

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
        evaluation_event = EvaluationEvent(enabled=False)
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
            return evaluation_event

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            evaluation_event = FeatureManager._check_default_disabled_variant(feature_flag)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
                evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
            evaluation_event.feature = feature_flag
            return evaluation_event

        evaluation_event = await self._check_feature_filters(feature_flag, evaluation_event, **kwargs)
        return self._assign_allocation(feature_flag, evaluation_event, **kwargs)

    def list_feature_flag_names(self):
        """
        List of all feature flag names.
        """
        return _list_feature_flag_names(self._configuration)
