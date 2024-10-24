# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import hashlib
import logging
from abc import ABC
from typing import List, Optional, Dict, Tuple, Any, Mapping
from ._models import FeatureFlag, Variant, VariantAssignmentReason, TargetingContext, EvaluationEvent, VariantReference


FEATURE_MANAGEMENT_KEY = "feature_management"
FEATURE_FLAG_KEY = "feature_flags"

PROVIDED_FEATURE_FILTERS = "feature_filters"
FEATURE_FILTER_NAME = "name"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"

FEATURE_FILTER_PARAMETERS = "parameters"


def _get_feature_flag(configuration: Mapping[str, Any], feature_flag_name: str) -> Optional[FeatureFlag]:
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


def _list_feature_flag_names(configuration: Mapping[str, Any]) -> List[str]:
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


class FeatureManagerBase(ABC):
    """
    Base class for Feature Manager. This class is responsible for all shared logic between the sync and async.
    """

    def __init__(self, configuration: Mapping[str, Any], **kwargs: Any):
        if configuration is None or not isinstance(configuration, Mapping):
            raise AttributeError("Configuration must be a non-empty dictionary")
        self._configuration = configuration
        self._cache: Dict[str, Optional[FeatureFlag]] = {}
        self._copy = configuration.get(FEATURE_MANAGEMENT_KEY)
        self._on_feature_evaluated = kwargs.pop("on_feature_evaluated", None)

    @staticmethod
    def _assign_default_disabled_variant(evaluation_event: EvaluationEvent) -> None:
        """
        A method called when the feature flag is disabled, to determine what the default variant should be. If there is
        no allocation, then None is set as the value of the variant in the EvaluationEvent.

        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED
        if not evaluation_event.feature or not evaluation_event.feature.allocation:
            return
        FeatureManagerBase._assign_variant_override(
            evaluation_event.feature.variants,
            evaluation_event.feature.allocation.default_when_disabled,
            False,
            evaluation_event,
        )

    @staticmethod
    def _assign_default_enabled_variant(evaluation_event: EvaluationEvent) -> None:
        """
        A method called when the feature flag is enabled, to determine what the default variant should be. If there is
        no allocation, then None is set as the value of the variant in the EvaluationEvent.

        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_ENABLED
        if not evaluation_event.feature or not evaluation_event.feature.allocation:
            return
        FeatureManagerBase._assign_variant_override(
            evaluation_event.feature.variants,
            evaluation_event.feature.allocation.default_when_enabled,
            True,
            evaluation_event,
        )

    @staticmethod
    def _assign_variant_override(
        variants: Optional[List[VariantReference]],
        default_variant_name: Optional[str],
        status: bool,
        evaluation_event: EvaluationEvent,
    ) -> None:
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
    def _is_targeted(context_id: str) -> float:
        """Determine if the user is targeted for the given context"""
        hashed_context_id = hashlib.sha256(context_id.encode()).digest()
        context_marker = int.from_bytes(hashed_context_id[:4], byteorder="little", signed=False)

        return (context_marker / (2**32 - 1)) * 100

    def _assign_variant(self, targeting_context: TargetingContext, evaluation_event: EvaluationEvent) -> None:
        """
        Assign a variant to the user based on the allocation.

        :param TargetingContext targeting_context: Targeting context.
        :param EvaluationEvent evaluation_event: Evaluation event object.
        """
        feature_flag = evaluation_event.feature
        variant_name = None
        if not feature_flag or not feature_flag.variants or not feature_flag.allocation:
            return

        allocation = feature_flag.allocation
        groups = targeting_context.groups

        if allocation.user and targeting_context.user_id:
            for user_allocation in allocation.user:
                if targeting_context.user_id in user_allocation.users:
                    evaluation_event.reason = VariantAssignmentReason.USER
                    variant_name = user_allocation.variant

        if not variant_name and allocation.group and groups:
            for group_allocation in allocation.group:
                if any(group in group_allocation.groups for group in groups):
                    evaluation_event.reason = VariantAssignmentReason.GROUP
                    variant_name = group_allocation.variant

        if not variant_name and allocation.percentile:
            seed = allocation.seed or f"allocation\n{feature_flag.name}"
            context_id = f"{targeting_context.user_id}\n{seed}"
            box: float = self._is_targeted(context_id)
            for percentile_allocation in allocation.percentile:
                percentile_to: int = percentile_allocation.percentile_to
                if (box == 100 and percentile_to == 100) or (
                    percentile_allocation.percentile_from <= box < percentile_to
                ):
                    evaluation_event.reason = VariantAssignmentReason.PERCENTILE
                    variant_name = percentile_allocation.variant
                    break

        if not variant_name:
            FeatureManagerBase._assign_default_enabled_variant(evaluation_event)
            if feature_flag.allocation:
                evaluation_event.variant = self._variant_name_to_variant(
                    feature_flag, feature_flag.allocation.default_when_enabled
                )
                return

        evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)
        if feature_flag.variants:
            FeatureManagerBase._assign_variant_override(feature_flag.variants, variant_name, True, evaluation_event)

    def _variant_name_to_variant(self, feature_flag: FeatureFlag, variant_name: Optional[str]) -> Optional[Variant]:
        """
        Get the variant object from the variant name.

        :param FeatureFlag feature_flag: Feature flag object.
        :param str variant_name: Name of the variant.
        :return: Variant object.
        """
        if not feature_flag.variants or not variant_name:
            return None

        for variant_reference in feature_flag.variants:
            if variant_reference.name == variant_name:
                return Variant(variant_reference.name, variant_reference.configuration_value)
        return None

    def _build_targeting_context(self, args: Tuple[Any]) -> TargetingContext:
        """
        Builds a TargetingContext, either returns a provided context, takes the provided user_id to make a context, or
        returns an empty context.

        :param args: Arguments to build the TargetingContext.
        :return: TargetingContext
        """
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, str):
                return TargetingContext(user_id=arg, groups=[])
            if isinstance(arg, TargetingContext):
                return arg
        return TargetingContext()

    def _assign_allocation(self, evaluation_event: EvaluationEvent, targeting_context: TargetingContext) -> None:
        feature_flag = evaluation_event.feature
        if not feature_flag:
            return

        if not feature_flag.variants or not feature_flag.allocation:
            return

        if not evaluation_event.enabled:
            FeatureManagerBase._assign_default_disabled_variant(evaluation_event)
            evaluation_event.variant = self._variant_name_to_variant(
                feature_flag, feature_flag.allocation.default_when_disabled
            )
            return

        self._assign_variant(targeting_context, evaluation_event)

    def _check_feature_base(self, feature_flag_id: str) -> Tuple[EvaluationEvent, bool]:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: The evaluation event and if the feature filters need to be checked.
        :rtype: evaluation_event, bool
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
            return evaluation_event, True

        if not feature_flag.enabled:
            # Feature flags that are disabled are always disabled
            self._assign_default_disabled_variant(evaluation_event)
            if feature_flag.allocation:
                variant_name = feature_flag.allocation.default_when_disabled
                evaluation_event.variant = self._variant_name_to_variant(feature_flag, variant_name)

            # If a feature flag is disabled and override can't enable it
            evaluation_event.enabled = False
            return evaluation_event, True
        return evaluation_event, False

    def list_feature_flag_names(self) -> List[str]:
        """
        List of all feature flag names.
        """
        return _list_feature_flag_names(self._configuration)
