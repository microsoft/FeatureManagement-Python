# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import logging

try:
    from azure.monitor.events.extension import track_event

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
REASON = "Reason"

EVENT_NAME = "FeatureEvaluation"


def send_telemetry_appinsights(evaluation_event):
    """
    Send telemetry for feature evaluation events.
    """
    event = {}
    event[FEATURE_NAME] = evaluation_event.feature.name
    event[ENABLED] = str(evaluation_event.enabled)
    if evaluation_event.user:
        event[TARGETING_ID] = evaluation_event.user

    if evaluation_event.reason:
        event[VARIANT] = evaluation_event.variant.name
        event[REASON] = evaluation_event.reason.value
    if HAS_AZURE_MONITOR_EVENTS_EXTENSION:
        track_event(EVENT_NAME, event)
