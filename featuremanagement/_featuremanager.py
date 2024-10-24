# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from typing import cast, overload, Any, Optional, Dict, Mapping, List
from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._featurefilters import FeatureFilter
from ._models import EvaluationEvent, Variant, TargetingContext
from ._featuremanagerbase import (
    FeatureManagerBase,
    PROVIDED_FEATURE_FILTERS,
    REQUIREMENT_TYPE_ALL,
    FEATURE_FILTER_NAME,
)


class FeatureManager(FeatureManagerBase):
    """
    Feature Manager that determines if a feature flag is enabled for the given context.

    :param Mapping configuration: Configuration object.
    :keyword list[FeatureFilter] feature_filters: Custom filters to be used for evaluating feature flags.
    :keyword Callable[EvaluationEvent] on_feature_evaluated: Callback function to be called when a feature flag is
    evaluated.
    """

    def __init__(self, configuration: Mapping[str, Any], **kwargs: Any):
        super().__init__(configuration, **kwargs)
        self._filters: Dict[str, FeatureFilter] = {}
        filters = [TimeWindowFilter(), TargetingFilter()] + cast(
            List[FeatureFilter], kwargs.pop(PROVIDED_FEATURE_FILTERS, [])
        )

        for feature_filter in filters:
            if not isinstance(feature_filter, FeatureFilter):
                raise ValueError("Custom filter must be a subclass of FeatureFilter")
            self._filters[feature_filter.name] = feature_filter

    @overload  # type: ignore
    def is_enabled(self, feature_flag_id: str, user_id: str, **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """

    def is_enabled(self, feature_flag_id: str, *args: Any, **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """
        targeting_context = self._build_targeting_context(args)

        result = self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if (
            self._on_feature_evaluated
            and result.feature
            and result.feature.telemetry.enabled
            and callable(self._on_feature_evaluated)
        ):
            result.user = targeting_context.user_id
            self._on_feature_evaluated(result)
        return result.enabled

    @overload  # type: ignore
    def get_variant(self, feature_flag_id: str, user_id: str, **kwargs: Any) -> Optional[Variant]:
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: return: Variant instance.
        :rtype: Variant
        """

    def get_variant(self, feature_flag_id: str, *args: Any, **kwargs: Any) -> Optional[Variant]:
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag
        :keyword TargetingContext targeting_context: Targeting context.
        :return: Variant instance.
        :rtype: Variant
        """
        targeting_context = self._build_targeting_context(args)

        result = self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if (
            self._on_feature_evaluated
            and result.feature
            and result.feature.telemetry.enabled
            and callable(self._on_feature_evaluated)
        ):
            result.user = targeting_context.user_id
            self._on_feature_evaluated(result)
        return result.variant

    def _check_feature_filters(
        self, evaluation_event: EvaluationEvent, targeting_context: TargetingContext, **kwargs: Any
    ) -> None:
        feature_flag = evaluation_event.feature
        if not feature_flag:
            return
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

    def _check_feature(
        self, feature_flag_id: str, targeting_context: TargetingContext, **kwargs: Any
    ) -> EvaluationEvent:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param TargetingContext targeting_context: Targeting context.
        :return: EvaluationEvent for the given context.
        :rtype: EvaluationEvent
        """
        evaluation_event, done = super()._check_feature_base(feature_flag_id)

        if done:
            return evaluation_event

        self._check_feature_filters(evaluation_event, targeting_context, **kwargs)

        self._assign_allocation(evaluation_event, targeting_context)
        return evaluation_event
