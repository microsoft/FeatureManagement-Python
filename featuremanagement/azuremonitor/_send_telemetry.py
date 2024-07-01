# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import logging
from .._models import VariantAssignmentReason

try:
    from azure.monitor.events.extension import track_event as azure_monitor_track_event

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


def track_event(event_name, user, event_properties=None):
    """
    Track an event with the specified name and properties.

    :param str event_name: The name of the event.
    :param dict[str, str] event_properties: A dictionary of named string properties.
    """
    if not HAS_AZURE_MONITOR_EVENTS_EXTENSION:
        return
    if event_properties is None:
        event_properties = {}
    event_properties[TARGETING_ID] = user
    azure_monitor_track_event(event_name, event_properties)


def publish_telemetry(evaluation_event):
    """
    Publishes the telemetry for a feature's evaluation event.
    """
    if not HAS_AZURE_MONITOR_EVENTS_EXTENSION:
        return
    event = {}
    event[FEATURE_NAME] = evaluation_event.feature.name
    event[ENABLED] = str(evaluation_event.enabled)
    if evaluation_event.user:
        event[TARGETING_ID] = evaluation_event.user

    if evaluation_event.reason and evaluation_event.reason != VariantAssignmentReason.NONE:
        event[VARIANT] = evaluation_event.variant.name
        event[REASON] = evaluation_event.reason.value

    event["ETag"] = evaluation_event.feature.telemetry.metadata.get("etag", "")
    event["FeatureFlagReference"] = evaluation_event.feature.telemetry.metadata.get("feature_flag_reference", "")
    event["FeatureFlagId"] = evaluation_event.feature.telemetry.metadata.get("feature_flag_id", "")
    azure_monitor_track_event(EVENT_NAME, event)
