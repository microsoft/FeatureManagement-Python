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

    def __init__(self, feature_flag):
        """
        Initialize the EvaluationEvent.
        """
        self.feature = feature_flag
        self.user = ""
        self.enabled = False
        self.variant = None
        self.reason = None
