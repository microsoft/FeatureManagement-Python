# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Targeting context model for user and group targeting."""

from typing import NamedTuple


class _TargetingContextTuple(NamedTuple):
    """Tuple fields shared by targeting contexts."""

    user_id: str
    """
    The user ID.
    
    :type: str
    """

    groups: list[str]
    """
    The user's groups.
    
    :type: list[str]
    """


class TargetingContext(_TargetingContextTuple):
    """
    Represents the context for targeting a feature flag.

    :param str user_id: The user ID.
    :param groups: The user's groups. If omitted or None, a new empty list is created.
    :type groups: list[str] or None
    """

    __slots__ = ()

    _field_defaults: dict[str, str | None] = {"user_id": "", "groups": None}

    def __new__(cls, user_id: str = "", groups: list[str] | None = None) -> "TargetingContext":
        # Ensures that each instance gets its own list for groups, even if the default is used.
        return super().__new__(cls, user_id, groups if groups is not None else [])
