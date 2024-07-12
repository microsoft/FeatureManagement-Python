# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from logging import getLogger, INFO
from .._models import VariantAssignmentReason


_event_logger = getLogger(__name__)

try:
    from opentelemetry.sdk._logs import LoggingHandler

    HAS_OPENTELEMETRY_SDK = True
except ImportError:
    HAS_OPENTELEMETRY_SDK = False
    _event_logger.warning("opentelemetry-sdk is not installed. Telemetry will not be sent to Open Telemetry.")

try:
    from azure.monitor.events.extension import track_event as azure_monitor_track_event

    HAS_AZURE_MONITOR_EVENTS_EXTENSION = True
except ImportError:
    HAS_AZURE_MONITOR_EVENTS_EXTENSION = False

FEATURE_NAME = "FeatureName"
ENABLED = "Enabled"
TARGETING_ID = "TargetingId"
VARIANT = "Variant"
REASON = "VariantAssignmentReason"

EVENT_NAME = "FeatureEvaluation"

_event_logger.propagate = False


class _FeatureMnagementEventsExtension:
    _initialized = False

    @staticmethod
    def initialize():
        """
        Initializes the logger to use an OpenTelemetry logging handler, if not already initialized.
        """
        if not _FeatureMnagementEventsExtension._initialized:
            _event_logger.addHandler(LoggingHandler())
            _event_logger.setLevel(INFO)
            _FeatureMnagementEventsExtension._initialized = True


def track_event(event_name, user, event_properties=None):
    """
    Track an event with the specified name and properties.

    :param str event_name: The name of the event.
    :param str user: The user ID to associate with the event.
    :param dict[str, str] event_properties: A dictionary of named string properties.
    """
    if not HAS_OPENTELEMETRY_SDK:
        return
    if event_properties is None:
        event_properties = {}
    event_properties[TARGETING_ID] = user
    if HAS_AZURE_MONITOR_EVENTS_EXTENSION:
        azure_monitor_track_event(event_name, event_properties)
        return
    _FeatureMnagementEventsExtension.initialize()
    _event_logger.info(event_name, extra=event_properties)


def publish_telemetry(evaluation_event):
    """
    Publishes the telemetry for a feature's evaluation event.

    :param EvaluationEvent evaluation_event: The evaluation event to publish telemetry for.
    """
    if not HAS_OPENTELEMETRY_SDK:
        return
    event = {}
    event[FEATURE_NAME] = evaluation_event.feature.name
    event[ENABLED] = str(evaluation_event.enabled)

    if evaluation_event.reason and evaluation_event.reason != VariantAssignmentReason.NONE:
        event[VARIANT] = evaluation_event.variant.name
        event[REASON] = evaluation_event.reason.value

    event["ETag"] = evaluation_event.feature.telemetry.metadata.get("etag", "")
    event["FeatureFlagReference"] = evaluation_event.feature.telemetry.metadata.get("feature_flag_reference", "")
    event["FeatureFlagId"] = evaluation_event.feature.telemetry.metadata.get("feature_flag_id", "")
    track_event(EVENT_NAME, evaluation_event.user, event)
