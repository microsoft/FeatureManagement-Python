# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import logging
import hashlib
from collections.abc import Mapping
from typing import overload
from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._featurefilters import FeatureFilter
from ._models import FeatureFlag, Variant, EvaluationEvent, VaraintAssignmentReason, TargetingContext


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
    :keyword on_feature_evaluated: Callback function to be called when a feature flag is evaluated
    :paramtype on_feature_evaluated: Callable[EvaluationEvent]
    """

    def __init__(self, configuration, **kwargs):
        self._filters = {}
        if configuration is None or not isinstance(configuration, Mapping):
            raise AttributeError("Configuration must be a non-empty dictionary")
        self._configuration = configuration
        self._cache = {}
        self._copy = configuration.get(FEATURE_MANAGEMENT_KEY)
        self._on_feature_evaluated = kwargs.get("on_feature_evaluated", None)
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
        evaluation_event = EvaluationEvent(feature_flag=feature_flag)
        if not feature_flag.variants or not feature_flag.allocation:
            return None, evaluation_event
        if feature_flag.allocation.user and targeting_context.user_id:
            for user_allocation in feature_flag.allocation.user:
                if targeting_context.user_id in user_allocation.users:
                    evaluation_event.reason = VaraintAssignmentReason.USER
                    return user_allocation.variant, evaluation_event
        if feature_flag.allocation.group and len(targeting_context.groups) > 0:
            for group_allocation in feature_flag.allocation.group:
                for group in targeting_context.groups:
                    if group in group_allocation.groups:
                        evaluation_event.reason = VaraintAssignmentReason.GROUP
                        return group_allocation.variant, evaluation_event
        if feature_flag.allocation.percentile:
            context_id = targeting_context.user_id + "\n" + feature_flag.allocation.seed
            box = self._is_targeted(context_id)
            for percentile_allocation in feature_flag.allocation.percentile:
                if box == 100 and percentile_allocation.percentile_to == 100:
                    return percentile_allocation.variant
                if percentile_allocation.percentile_from <= box < percentile_allocation.percentile_to:
                    evaluation_event.reason = VaraintAssignmentReason.PERCENTILE
                    return percentile_allocation.variant, evaluation_event
        return None, evaluation_event

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

    @overload
    def is_enabled(self, feature_flag_id, user_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :param str user_id: User identifier
        :paramtype user_id: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """

    def is_enabled(self, feature_flag_id, *args, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: True if the feature flag is enabled for the given context
        :rtype: bool
        """
        targeting_context = TargetingContext()
        if len(args) == 1 and isinstance(args[0], str):
            targeting_context = TargetingContext(user_id=args[0], groups=[])
        elif len(args) == 1 and isinstance(args[0], TargetingContext):
            targeting_context = args[0]

        result = self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if self._on_feature_evaluated and result.feature.telemetry.enabled:
            result.user = targeting_context.user_id
            self._on_feature_evaluated(result)
        return result.enabled

    @overload
    def get_variant(self, feature_flag_id, user_id, **kwargs):
        """
        Determine the variant for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :param str user_id: User identifier
        :paramtype user_id: str
        :return: return: Variant instance
        :rtype: Variant
        """

    def get_variant(self, feature_flag_id, *args, **kwargs):
        """
        Determine the variant for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :kwyword targeting_context: Targeting context
        :paramtype TargetingContext: TargetingContext
        :return: Variant instance
        :rtype: Variant
        """
        targeting_context = TargetingContext()
        if len(args) == 1 and isinstance(args[0], str):
            targeting_context = TargetingContext(user_id=args[0], groups=[])
        elif len(args) == 1 and isinstance(args[0], TargetingContext):
            targeting_context = args[0]

        result = self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if self._on_feature_evaluated and result.feature.telemetry.enabled:
            result.user = targeting_context.user_id
            self._on_feature_evaluated(result)
        return result.variant

    def _check_feature_filters(self, feature_flag, evaluation_event, targeting_context, **kwargs):
        feature_conditions = feature_flag.conditions
        feature_filters = feature_conditions.client_filters

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
                if not self._filters[filter_name].evaluate(feature_filter, **kwargs):
                    evaluation_event.enabled = False
                    break
            elif self._filters[filter_name].evaluate(feature_filter, **kwargs):
                evaluation_event.enabled = True
                break
        return evaluation_event

    def _assign_allocation(self, feature_flag, evaluation_event, targeting_context):
        if feature_flag.allocation and feature_flag.variants:
            default_enabled = evaluation_event.enabled
            variant_name, evaluation_event = self._assign_variant(feature_flag, targeting_context)
            evaluation_event.enabled = default_enabled
            if variant_name:
                evaluation_event.enabled = FeatureManager._check_variant_override(
                    feature_flag.variants, variant_name, evaluation_event.enabled
                ).enabled
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

    def _check_feature(self, feature_flag_id, targeting_context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context

        :param str feature_flag_id: Name of the feature flag
        :paramtype feature_flag_id: str
        :return: True if the feature flag is enabled for the given context
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

        evaluation_event = self._check_feature_filters(feature_flag, evaluation_event, targeting_context, **kwargs)

        return self._assign_allocation(feature_flag, evaluation_event, targeting_context)

    def list_feature_flag_names(self):
        """
        List of all feature flag names
        """
        return _list_feature_flag_names(self._configuration)
