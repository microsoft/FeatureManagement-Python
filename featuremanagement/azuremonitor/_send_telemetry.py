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

EVENT_NAME = "FeatureEvaluation"

EVALUATION_EVENT_VERSION = "1.0.0"


def track_event(event_name: str, user: str, event_properties: Optional[Dict[str, Optional[str]]] = None) -> None:
    """
    Tracks an event with the specified name and properties.

    :param str event_name: The name of the event.
    :param str user: The user ID to associate with the event.
    :param dict[str, str] event_properties: A dictionary of named string properties.
    """
    if not HAS_AZURE_MONITOR_EVENTS_EXTENSION:
        return
    if event_properties is None:
        event_properties = {}
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
    event: Dict[str, Optional[str]] = {}
    if not evaluation_event.feature:
        return
    event[FEATURE_NAME] = evaluation_event.feature.name
    event[ENABLED] = str(evaluation_event.enabled)
    event["Version"] = EVALUATION_EVENT_VERSION

    # VariantAllocationPercentage
    if evaluation_event.reason and evaluation_event.reason != VariantAssignmentReason.NONE:
        if evaluation_event.variant:
            event[VARIANT] = evaluation_event.variant.name
        event[REASON] = evaluation_event.reason.value

        if evaluation_event.reason == VariantAssignmentReason.DEFAULT_WHEN_ENABLED:
            allocation_percentage = 0

            if evaluation_event.feature.allocation and evaluation_event.feature.allocation.percentile:
                for allocation in evaluation_event.feature.allocation.percentile:
                    if (
                        evaluation_event.variant
                        and allocation.variant == evaluation_event.variant.name
                        and allocation.percentile_to
                    ):
                        allocation_percentage += allocation.percentile_to - allocation.percentile_from

            event["VariantAssignmentPercentage"] = str(100 - allocation_percentage)
        elif evaluation_event.reason == VariantAssignmentReason.PERCENTILE:
            if evaluation_event.feature.allocation and evaluation_event.feature.allocation.percentile:
                allocation_percentage = 0
                for allocation in evaluation_event.feature.allocation.percentile:
                    if (
                        evaluation_event.variant
                        and allocation.variant == evaluation_event.variant.name
                        and allocation.percentile_to
                    ):
                        allocation_percentage += allocation.percentile_to - allocation.percentile_from
                event["VariantAssignmentPercentage"] = str(allocation_percentage)

    # DefaultWhenEnabled
    if evaluation_event.feature.allocation and evaluation_event.feature.allocation.default_when_enabled:
        event["DefaultWhenEnabled"] = evaluation_event.feature.allocation.default_when_enabled

    if evaluation_event.feature.telemetry:
        for metadata_key, metadata_value in evaluation_event.feature.telemetry.metadata.items():
            if metadata_key not in event:
                event[metadata_key] = metadata_value
    track_event(EVENT_NAME, evaluation_event.user, event_properties=event)
