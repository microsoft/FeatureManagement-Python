# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

from ._send_telemetry_appinsights import send_telemetry, track_event


__all__ = [
    "send_telemetry",
    "track_event",
]
