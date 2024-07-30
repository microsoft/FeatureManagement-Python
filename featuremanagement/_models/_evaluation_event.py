# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass
from typing import Optional
from ._feature_flag import FeatureFlag
from ._variant_assignment_reason import VariantAssignmentReason
from ._variant import Variant


@dataclass
class EvaluationEvent:
    """
    Represents a feature flag evaluation event.
    """

    def __init__(self, feature_flag: Optional[FeatureFlag]):
        """
        Initialize the EvaluationEvent.
        """
        self.feature = feature_flag
        self.user = ""
        self.enabled = False
        self.variant: Optional[Variant] = None
        self.reason: Optional[VariantAssignmentReason] = None
