# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from ._send_telemetry import publish_telemetry, track_event, attach_targeting_info, TargetingSpanProcessor


__all__ = [
    "publish_telemetry",
    "track_event",
    "attach_targeting_info",
    "TargetingSpanProcessor",
]
