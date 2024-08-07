# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import inspect
import logging
from typing import cast, overload, Mapping, Dict, Any, Optional, List
from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._featurefilters import FeatureFilter
from .._models import EvaluationEvent, TargetingContext, Variant
from .._featuremanagerbase import (
    _get_feature_flag,
    FeatureManagerBase,
    PROVIDED_FEATURE_FILTERS,
    FEATURE_MANAGEMENT_KEY,
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
    async def is_enabled(self, feature_flag_id: str, user_id: str, **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """

    async def is_enabled(self, feature_flag_id: str, *args: Any, **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :return: True if the feature flag is enabled for the given context.
        :rtype: bool
        """
        targeting_context = self._build_targeting_context(args)

        result = await self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if self._on_feature_evaluated and result.feature and result.feature.telemetry.enabled:
            result.user = targeting_context.user_id
            if inspect.iscoroutinefunction(self._on_feature_evaluated):
                await self._on_feature_evaluated(result)
            elif callable(self._on_feature_evaluated):
                self._on_feature_evaluated(result)
        return result.enabled

    @overload  # type: ignore
    async def get_variant(self, feature_flag_id: str, user_id: str, **kwargs: Any) -> Optional[Variant]:
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param str user_id: User identifier.
        :return: return: Variant instance.
        :rtype: Variant
        """

    async def get_variant(self, feature_flag_id: str, *args: Any, **kwargs: Any) -> Optional[Variant]:
        """
        Determine the variant for the given context.

        :param str feature_flag_id: Name of the feature flag
        :keyword TargetingContext targeting_context: Targeting context.
        :return: Variant instance.
        :rtype: Variant
        """
        targeting_context = self._build_targeting_context(args)

        result = await self._check_feature(feature_flag_id, targeting_context, **kwargs)
        if self._on_feature_evaluated and result.feature and result.feature.telemetry.enabled:
            result.user = targeting_context.user_id
            if inspect.iscoroutinefunction(self._on_feature_evaluated):
                await self._on_feature_evaluated(result)
            elif callable(self._on_feature_evaluated):
                self._on_feature_evaluated(result)
        return result.variant

    async def _check_feature_filters(
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
                if not await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                    evaluation_event.enabled = False
                    break
            elif await self._filters[filter_name].evaluate(feature_filter, **kwargs):
                evaluation_event.enabled = True
                break

    async def _check_feature(
        self, feature_flag_id: str, targeting_context: TargetingContext, **kwargs: Any
    ) -> EvaluationEvent:
        """
        Determine if the feature flag is enabled for the given context.

        :param str feature_flag_id: Name of the feature flag.
        :param TargetingContext targeting_context: Targeting context.
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

        await self._check_feature_filters(evaluation_event, targeting_context, **kwargs)

        self._assign_allocation(evaluation_event, targeting_context)
        return evaluation_event
