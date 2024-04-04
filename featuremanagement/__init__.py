# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from ._featuremanager import FeatureManager
from ._featurefilters import FeatureFilter
from ._defaultfilters import TimeWindowFilter, TargetingFilter
from ._models import FeatureFlag, Variant, EvaluationEvent, VaraintAssignmentReason
from ._send_telemetry_appinsights import send_telemetry_appinsights

from ._version import VERSION

__version__ = VERSION
__all__ = [
    "FeatureManager",
    "TimeWindowFilter",
    "TargetingFilter",
    "FeatureFilter",
    "FeatureFlag",
    "Variant",
    "EvaluationEvent",
    "VaraintAssignmentReason",
    "send_telemetry_appinsights",
]
