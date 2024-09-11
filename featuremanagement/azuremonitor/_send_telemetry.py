# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import logging
from typing import Dict, Optional
from .._models import VariantAssignmentReason, EvaluationEvent
import hashlib
import base64

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


def _generate_allocation_id(feature):
    """
    Generates an allocation ID for the specified feature.

    :param FeatureFlag feature: The feature to generate an allocation ID for.
    :rtype: str
    :return: The allocation ID.
    """

    allocation_id = ""
    allocated_variants = []

    if feature.allocation:
        # Seed
        allocation_id = f"seed={feature.allocation._seed or ''}"

        # DefaultWhenEnabled
        if feature.allocation._default_when_enabled:
            allocated_variants.append(feature.allocation._default_when_enabled)

        allocation_id += f"\ndefault_when_enabled={feature.allocation._default_when_enabled or ''}"

        # Percentile
        allocation_id += "\npercentiles="

        if feature.allocation._percentile:
            percentile_allocations = sorted(
                (x for x in feature.allocation._percentile if x.percentile_from != x.percentile_to),
                key=lambda x: x.percentile_from,
            )

            allocated_variants.extend(pa.variant for pa in percentile_allocations)

            allocation_id += ";".join(
                f"{pa.percentile_from},{pa.variant},{pa.percentile_to}" for pa in percentile_allocations
            )
    else:
        allocation_id = "seed=\ndefault_when_enabled=\npercentiles="

    # Variants
    allocation_id += "\nvariants="

    if allocated_variants:
        variants = sorted((v for v in feature._variants if v.name in allocated_variants), key=lambda v: v.name)
        allocation_id += ";".join(f"{v.name},{v.configuration_value}" for v in variants)

    if not allocated_variants and (feature.allocation or feature.allocation._seed):
        return None

    # Create a sha256 hash of the allocation_id
    hash_object = hashlib.sha256(allocation_id.encode())
    hash_digest = hash_object.digest()

    # Encode the first 15 bytes in base64 url
    allocation_id_hash = base64.urlsafe_b64encode(hash_digest[:15]).decode("utf-8")
    return allocation_id_hash


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
    event = {}
    if evaluation_event.feature:
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

            if evaluation_event.feature.allocation._percentile:

                for allocation in evaluation_event.feature.allocation._percentile:
                    if allocation.variant == evaluation_event.variant.name:
                        allocation_percentage += allocation.percentile_to - allocation.percentile_from

            event["VariantAssignmentPercentage"] = 100 - allocation_percentage
        elif evaluation_event.reason == VariantAssignmentReason.PERCENTILE:
            if evaluation_event.feature.allocation._percentile:
                allocation_percentage = 0
                for allocation in evaluation_event.feature.allocation._percentile:
                    if allocation.variant == evaluation_event.variant.name:
                        allocation_percentage += allocation.percentile_to - allocation.percentile_from
                event["VariantAssignmentPercentage"] = allocation_percentage

    # DefaultWhenEnabled
    if evaluation_event.feature.allocation._default_when_enabled:
        event["DefaultWhenEnabled"] = evaluation_event.feature.allocation._default_when_enabled

    # AllocationId
    allocation_id = _generate_allocation_id(evaluation_event.feature)
    if allocation_id:
        event["AllocationId"] = allocation_id

    if evaluation_event.feature and evaluation_event.feature.telemetry:
        for metadata_key, metadata_value in evaluation_event.feature.telemetry.metadata.items():
            if metadata_key not in event:
                event[metadata_key] = metadata_value
    track_event(EVENT_NAME, evaluation_event.user, event_properties=event)
