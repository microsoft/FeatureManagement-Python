# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Telemetry publishing for feature evaluation events."""

import logging
import inspect
from typing import Any, Callable, Dict, Optional
from .._models import VariantAssignmentReason, EvaluationEvent, TargetingContext

logger = logging.getLogger(__name__)

# Set up a separate logger for feature-evaluation telemetry events to avoid propagating to the root logger
_event_logger = logging.getLogger(__name__ + ".events")
_event_logger.propagate = False

try:
    from logging import INFO
    from opentelemetry.instrumentation.logging.handler import LoggingHandler
    from opentelemetry.sdk.trace import SpanProcessor

    HAS_OPENTELEMETRY_LOGGING = True
except ImportError:
    HAS_OPENTELEMETRY_LOGGING = False
    LoggingHandler = object  # type: ignore
    SpanProcessor = object  # type: ignore


_events_logger_initialized = False

def _initialize_event_logger() -> None:
    global _events_logger_initialized
    if _events_logger_initialized:
        return

    if not HAS_OPENTELEMETRY_LOGGING:
        logger.warning(
            "OpenTelemetry logging handler is not installed. Telemetry will not be sent to Application Insights."
        )
        return

    _event_logger.addHandler(LoggingHandler())
    _event_logger.setLevel(INFO)
    _events_logger_initialized = True

FEATURE_NAME = "FeatureName"
ENABLED = "Enabled"
TARGETING_ID = "TargetingId"
VARIANT = "Variant"
REASON = "VariantAssignmentReason"

DEFAULT_WHEN_ENABLED = "DefaultWhenEnabled"
VERSION = "Version"
VARIANT_ASSIGNMENT_PERCENTAGE = "VariantAssignmentPercentage"
MICROSOFT_TARGETING_ID = "Microsoft.TargetingId"

EVENT_NAME = "FeatureEvaluation"

EVALUATION_EVENT_VERSION = "1.0.0"


def track_event(event_name: str, user: str, event_properties: Optional[Dict[str, Optional[str]]] = None) -> None:
    """
    Tracks an event with the specified name and properties.

    :param str event_name: The name of the event.
    :param str user: The user ID to associate with the event.
    :param dict[str, str] event_properties: A dictionary of named string properties.
    """
    if not HAS_OPENTELEMETRY_LOGGING:
        return

    _initialize_event_logger()

    event_properties = event_properties or {}

    if user:
        event_properties[TARGETING_ID] = user

    # Azure Monitor exporter maps this attribute to customEvent telemetry name.
    custom_event_attributes = {
        **event_properties,
        "microsoft.custom_event.name": event_name,
    }
    _event_logger.info(event_name, extra=custom_event_attributes)


def publish_telemetry(evaluation_event: EvaluationEvent) -> None:
    """
    Publishes the telemetry for a feature's evaluation event.

    :param EvaluationEvent evaluation_event: The evaluation event to publish telemetry for.
    """
    if not HAS_OPENTELEMETRY_LOGGING:
        return

    feature = evaluation_event.feature

    if not feature:
        return

    event: Dict[str, Optional[str]] = {
        FEATURE_NAME: feature.name,
        ENABLED: str(evaluation_event.enabled),
        VERSION: EVALUATION_EVENT_VERSION,
    }

    reason = evaluation_event.reason
    variant = evaluation_event.variant

    event[REASON] = reason.value

    if variant:
        event[VARIANT] = variant.name

    # VariantAllocationPercentage
    allocation_percentage = 0
    if reason == VariantAssignmentReason.DEFAULT_WHEN_ENABLED:
        event[VARIANT_ASSIGNMENT_PERCENTAGE] = str(100)
        if feature.allocation:
            for allocation in feature.allocation.percentile:
                allocation_percentage += allocation.percentile_to - allocation.percentile_from
            event[VARIANT_ASSIGNMENT_PERCENTAGE] = str(100 - allocation_percentage)
    elif reason == VariantAssignmentReason.PERCENTILE:
        if feature.allocation and feature.allocation.percentile:
            for allocation in feature.allocation.percentile:
                if variant and allocation.variant == variant.name:
                    allocation_percentage += allocation.percentile_to - allocation.percentile_from
            event[VARIANT_ASSIGNMENT_PERCENTAGE] = str(allocation_percentage)

    # DefaultWhenEnabled
    if feature.allocation and feature.allocation.default_when_enabled:
        event[DEFAULT_WHEN_ENABLED] = feature.allocation.default_when_enabled

    if feature.telemetry:
        for metadata_key, metadata_value in feature.telemetry.metadata.items():
            if metadata_key not in event:
                event[metadata_key] = metadata_value

    track_event(EVENT_NAME, evaluation_event.user, event_properties=event)


class TargetingSpanProcessor(SpanProcessor):
    """
    A custom SpanProcessor that attaches the targeting ID to the span and baggage when a new span is started.
    :keyword Callable[[], TargetingContext] targeting_context_accessor: Callback function to get the current targeting
    context if one isn't provided.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._targeting_context_accessor: Optional[Callable[[], TargetingContext]] = kwargs.pop(
            "targeting_context_accessor", None
        )

    def on_start(self, span: Any, parent_context: Optional[Any] = None) -> None:  # pylint: disable=unused-argument
        """
        Attaches the targeting ID to the span and baggage when a new span is started.

        :param Span span: The span that was started.
        :param parent_context: The parent context of the span.
        """
        if not HAS_OPENTELEMETRY_LOGGING:
            logger.warning("OpenTelemetry logging handler is not installed.")
            return
        if self._targeting_context_accessor and callable(self._targeting_context_accessor):
            if inspect.iscoroutinefunction(self._targeting_context_accessor):
                logger.warning("Async targeting_context_accessor is not supported.")
                return
            targeting_context = self._targeting_context_accessor()
            if not targeting_context or not isinstance(targeting_context, TargetingContext):
                logger.warning(
                    "targeting_context_accessor did not return a TargetingContext. Received type %s.",
                    type(targeting_context),
                )
                return
            if not targeting_context.user_id:
                logger.debug("TargetingContext does not have a user ID.")
                return
            span.set_attribute(TARGETING_ID, targeting_context.user_id)
