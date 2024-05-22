# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from typing import NamedTuple, List


class TargetingContext(NamedTuple):
    """
    Represents the context for targeting a feature flag.
    """

    # The user ID
    user_id: str = ""
    """
    The user ID.
    
    :type: str
    """

    # The users groups
    groups: List[str] = []
    """
    The users groups.
    
    :type: List[str]
    """
