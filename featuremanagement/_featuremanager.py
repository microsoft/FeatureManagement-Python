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
from ._models import FeatureFlag, Variant, EvaluationEvent, VariantAssignmentReason, TargetingContext


FEATURE_MANAGEMENT_KEY = "feature_management"
FEATURE_FLAG_KEY = "feature_flags"

PROVIDED_FEATURE_FILTERS = "feature_filters"
FEATURE_FILTER_NAME = "name"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"

FEATURE_FILTER_PARAMETERS = "parameters"


def _get_feature_flag(configuration, feature_flag_name):
    """
    Gets the FeatureFlag json from the configuration, if it exists it gets converted to a FeatureFlag object.

    :param Mapping configuration: Configuration object.
    :param str feature_flag_name: Name of the feature flag.
    :return: FeatureFlag
    :rtype: FeatureFlag
    """
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
    List of all feature flag names.

    :param Mapping configuration: Configuration object.
    :return: List of feature flag names.
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
    def _check_default_disabled_variant(evaluation_event):
        """
        A method called when the feature flag is disabled, to determine what the default variant should be. If there is
        no allocation, then None is set as the value of the variant in the EvaluationEvent.

        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED
        if not evaluation_event.feature.allocation:
            evaluation_event.enabled = False
            return
        FeatureManager._check_variant_override(
            evaluation_event.feature.variants,
            evaluation_event.feature.allocation.default_when_disabled,
            False,
            evaluation_event,
        )

    @staticmethod
    def _check_default_enabled_variant(evaluation_event):
        """
        A method called when the feature flag is enabled, to determine what the default variant should be. If there is
        no allocation, then None is set as the value of the variant in the EvaluationEvent.

        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_ENABLED
        if not evaluation_event.feature.allocation:
            evaluation_event.enabled = True
            return
        FeatureManager._check_variant_override(
            evaluation_event.feature.variants,
            evaluation_event.feature.allocation.default_when_enabled,
            True,
            evaluation_event,
        )

    @staticmethod
    def _check_variant_override(variants, default_variant_name, status, evaluation_event):
        """
        A method to check if a variant is overridden to be enabled or disabled by the variant.

        :param list[Variant] variants: List of variants.
        :param str default_variant_name: Name of the default variant.
        :param bool status: Status of the feature flag.
        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        if not variants or not default_variant_name:
            evaluation_event.enabled = status
            return
        for variant in variants:
            if variant.name == default_variant_name:
                if variant.status_override == "Enabled":
                    evaluation_event.enabled = True
                    return
                if variant.status_override == "Disabled":
                    evaluation_event.enabled = False
                    return
        evaluation_event.enabled = status

    @staticmethod
    def _is_targeted(context_id):
        """Determine if the user is targeted for the given context"""
        hashed_context_id = hashlib.sha256(context_id.encode()).digest()
        context_marker = int.from_bytes(hashed_context_id[:4], byteorder="little", signed=False)

        return (context_marker / (2**32 - 1)) * 100

    def _assign_variant(self, feature_flag, targeting_context, evaluation_event):
        """
        Assign a variant to the user based on the allocation.

        :param TargetingContext targeting_context: Targeting context.
        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        feature = evaluation_event.feature
        variant_name = None
        if not feature.variants or not feature.allocation:
            return
        if feature.allocation.user and targeting_context.user_id:
            for user_allocation in feature.allocation.user:
                if targeting_context.user_id in user_allocation.users:
                    evaluation_event.reason = VariantAssignmentReason.USER
                    variant_name = user_allocation.variant
        elif feature.allocation.group and len(targeting_context.groups) > 0:
            for group_allocation in feature.allocation.group:
                for group in targeting_context.groups:
                    if group in group_allocation.groups:
                        evaluation_event.reason = VariantAssignmentReason.GROUP
                        variant_name = group_allocation.variant
        elif feature.allocation.percentile:
            context_id = targeting_context.user_id + "\n" + feature.allocation.seed
            box = self._is_targeted(context_id)
            for percentile_allocation in feature.allocation.percentile:
                if box == 100 and percentile_allocation.percentile_to == 100:
                    variant_name = percentile_allocation.variant
                if percentile_allocation.percentile_from <= box < percentile_allocation.percentile_to:
                    evaluation_event.reason = VariantAssignmentReason.PERCENTILE
                    variant_name = percentile_allocation.variant
        if not variant_name:
            FeatureManager._check_default_enabled_variant(evaluation_event)
            evaluation_event.variant = self._variant_name_to_variant(
                feature_flag, feature_flag.allocation.default_when_enabled
            )
            return
        evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
        FeatureManager._check_variant_override(feature_flag.variants, variant_name, True, evaluation_event)

    def _variant_name_to_variant(self, feature_flag, variant_name):
        """
        Get the variant object from the variant name.

        :param FeatureFlag feature_flag: Feature flag object.
        :param str variant_name: Name of the variant.
        :return: Variant object.
        """
        if not feature_flag.variants:
            return None
        if not variant_name:
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
    def is_enabled(self, feature_flag_id, user_id, **kwargs):
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """

    def is_enabled(self, feature_flag_id, *args, **kwargs):
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """
        targeting_context = self._build_targeting_context(args)

        result = self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if self._on_feature_evaluated and result.feature.telemetry.enabled:
            result.user = targeting_context.user_id
            self._on_feature_evaluated(result)
        return result.enabled

    @overload
    def get_variant(self, feature_flag_id, user_id, **kwargs):
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: return: Variant instance.
        :rtype: Variant
        """

    def get_variant(self, feature_flag_id, *args, **kwargs):
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag
        :keyword TargetingContext targeting_context: Targeting context.
        :return: Variant instance.
        :rtype: Variant
        """
        targeting_context = self._build_targeting_context(args)

        result = self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if self._on_feature_evaluated and result.feature.telemetry.enabled:
            result.user = targeting_context.user_id
            self._on_feature_evaluated(result)
        return result.variant

    def _check_feature_filters(self, evaluation_event, targeting_context, **kwargs):
        feature_flag = evaluation_event.feature
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

    def _assign_allocation(self, evaluation_event, targeting_context):
        feature_flag = evaluation_event.feature
        if feature_flag.variants:
            if not feature_flag.allocation:
                if evaluation_event.enabled:
                    evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_ENABLED
                    return
                evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED
                return
            if not evaluation_event.enabled:
                FeatureManager._check_default_disabled_variant(evaluation_event)
                evaluation_event.variant = self._variant_name_to_variant(
                    feature_flag, feature_flag.allocation.default_when_disabled
                )
                return

            self._assign_variant(feature_flag, targeting_context, evaluation_event)

    def _check_feature(self, feature_flag_id, targeting_context, **kwargs):
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

        evaluation_event = EvaluationEvent(feature_flag)
        if not feature_flag:
            logging.warning("Feature flag %s not found", feature_flag_id)
            # Unknown feature flags are disabled by default
            return evaluation_event

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            FeatureManager._check_default_disabled_variant(evaluation_event)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
                evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
            evaluation_event.feature = feature_flag

            # If a feature flag is disabled and override can't enable it
            evaluation_event.enabled = False
            return evaluation_event

        self._check_feature_filters(evaluation_event, targeting_context, **kwargs)

        self._assign_allocation(evaluation_event, targeting_context)
        return evaluation_event

    def list_feature_flag_names(self):
        """
        List of all feature flag names.
        """
        return _list_feature_flag_names(self._configuration)
