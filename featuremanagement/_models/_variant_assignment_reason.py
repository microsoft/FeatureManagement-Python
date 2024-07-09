# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from enum import Enum


class VariantAssignmentReason(Enum):
    """
    Represents an assignment reason.
    """

    NONE = "None"
    DEFAULT_WHEN_DISABLED = "DefaultWhenDisabled"
    DEFAULT_WHEN_ENABLED = "DefaultWhenEnabled"
    USER = "User"
    GROUP = "Group"
    PERCENTILE = "Percentile"
