# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass


@dataclass
class Telemetry:
    """
    Represents the telemetry for a feature flag
    """

    enbled: bool = False
    metadata: dict = None
