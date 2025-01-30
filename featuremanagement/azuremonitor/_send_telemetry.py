# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import logging
from typing import Dict, Optional
from .._models import VariantAssignmentReason, EvaluationEvent

try:
    from azure.monitor.events.extension import track_event as azure_monitor_track_event  # type: ignore
    from opentelemetry import trace, baggage, context
    from opentelemetry.context.context import Context
    from opentelemetry.sdk.trace import Span, SpanProcessor

    HAS_AZURE_MONITOR_EVENTS_EXTENSION = True
except ImportError:
    HAS_AZURE_MONITOR_EVENTS_EXTENSION = False
    logging.warning(
        "azure-monitor-events-extension is not installed. Telemetry will not be sent to Application Insights."
    )

FEATURE_NAME = "FeatureName"
ENABLED = "Enabled"
TARGETING_ID = "TargetingId"
VARIANT = "Variant"
REASON = "VariantAssignmentReason"

DEFAULT_WHEN_ENABLED = "DefaultWhenEnabled"
VERSION = "Version"
VARIANT_ASSIGNMENT_PERCENTAGE = "VariantAssignmentPercentage"
MICROSOFT_TARGETING_ID = "Microsoft.TargetingId"
SPAN = "Span"

EVENT_NAME = "FeatureEvaluation"

EVALUATION_EVENT_VERSION = "1.1.0"


def track_event(event_name: str, user: str, event_properties: Optional[Dict[str, Optional[str]]] = None) -> None:
    """
    Tracks an event with the specified name and properties.

    :param str event_name: The name of the event.
    :param str user: The user ID to associate with the event.
    :param dict[str, str] event_properties: A dictionary of named string properties.
    """
    if not HAS_AZURE_MONITOR_EVENTS_EXTENSION:
        return

    event_properties = event_properties or {}

    if user:
        event_properties[TARGETING_ID] = user

    azure_monitor_track_event(event_name, event_properties)


def publish_telemetry(evaluation_event: EvaluationEvent) -> None:
    """
    Publishes the telemetry for a feature's evaluation event.

    :param EvaluationEvent evaluation_event: The evaluation event to publish telemetry for.
    """
    if not HAS_AZURE_MONITOR_EVENTS_EXTENSION:
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


def attach_targeting_info(targeting_id: str) -> None:
    """
    Attaches the targeting ID to the current span and baggage.

    :param str targeting_id: The targeting ID to attach.
    """
    context.attach(baggage.set_baggage(MICROSOFT_TARGETING_ID, targeting_id))
    trace.get_current_span().set_attribute(TARGETING_ID, targeting_id)


class TargetingSpanProcessor(SpanProcessor):
    """
    A custom SpanProcessor that attaches the targeting ID to the span and baggage when a new span is started.
    """

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        """
        Attaches the targeting ID to the span and baggage when a new span is started.

        :param Span span: The span that was started.
        :param parent_context: The parent context of the span.
        """
        target_baggage = baggage.get_baggage(MICROSOFT_TARGETING_ID, parent_context)
        if target_baggage is not None and isinstance(target_baggage, str):
            span.set_attribute(TARGETING_ID, target_baggage)
