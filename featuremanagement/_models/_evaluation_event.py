# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass


@dataclass
class EvaluationEvent:
    """
    Represents a feature flag evaluation event.
    """

    def __init__(self, *, enabled=False, feature_flag=None):
        """
        Initialize the EvaluationEvent.
        """
        self.feature = feature_flag
        self.user = ""
        self.enabled = enabled
        self.variant = None
        self.reason = None
