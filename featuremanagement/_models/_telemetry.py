# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from typing import Dict
from dataclasses import dataclass, field


@dataclass
class Telemetry:
    """
    Represents the telemetry configuration for a feature flag.
    """

    enabled: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)
