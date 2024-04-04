# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from enum import Enum


class VaraintAssignmentReason(Enum):
    """
    Represents an assignment reason
    """

    NONE = "NONE"
    DEFAULT_WHEN_DISABLED = "DEFAULT_WHEN_DISABLED"
    DEFAULT_WHEN_ENABLED = "DEFAULT_WHEN_ENABLED"
    USER = "USER"
    GROUP = "GROUP"
    PERCENTILE = "PERCENTILE"
