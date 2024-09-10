# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from typing import cast, List, Optional, Mapping, Dict, Any, Union
from dataclasses import dataclass
from ._constants import DEFAULT_WHEN_ENABLED, DEFAULT_WHEN_DISABLED, USER, GROUP, PERCENTILE, SEED


@dataclass
class UserAllocation:
    """
    Represents a user allocation.
    """

    variant: str
    users: List[str]


@dataclass
class GroupAllocation:
    """
    Represents a group allocation.
    """

    variant: str
    groups: List[str]


class PercentileAllocation:
    """
    Represents a percentile allocation.
    """

    def __init__(self) -> None:
        self._variant: Optional[str] = None
        self._percentile_from: int = 0
        self._percentile_to: Optional[int] = None

    @classmethod
    def convert_from_json(cls, json: Mapping[str, Union[str, int]]) -> "PercentileAllocation":
        """
        Convert a JSON object to PercentileAllocation.

        :param dict json: JSON object.
        :return: PercentileAllocation
        :rtype: PercentileAllocation
        """
        if not json:
            raise ValueError("Percentile allocation is not valid.")
        user_allocation = cls()

        variant = json.get("variant")
        if not variant or not isinstance(variant, str):
            raise ValueError("Percentile allocation does not have a valid assigned variant.")
        user_allocation._variant = variant

        percentile_from = json.get("from", 0)
        if not isinstance(percentile_from, int):
            raise ValueError("Percentile allocation does not have a valid starting percentile.")
        user_allocation._percentile_from = percentile_from

        percentile_to = json.get("to")
        if not percentile_to or not isinstance(percentile_to, int):
            raise ValueError("Percentile allocation does not have a valid ending percentile.")
        user_allocation._percentile_to = percentile_to
        return user_allocation

    @property
    def variant(self) -> Optional[str]:
        """
        Get the variant for the allocation.

        :return: Variant for the allocation.
        :rtype: str
        """
        return self._variant

    @property
    def percentile_from(self) -> int:
        """
        Get the starting percentile for the allocation.

        :return: Starting percentile for the allocation.
        :rtype: int
        """
        return self._percentile_from

    @property
    def percentile_to(self) -> Optional[int]:
        """
        Get the ending percentile for the allocation.

        :return: Ending percentile for the allocation.
        :rtype: int
        """
        return self._percentile_to


class Allocation:
    """
    Represents an allocation configuration for a feature flag.
    """

    def __init__(self, feature_name: str) -> None:
        self._default_when_enabled = None
        self._default_when_disabled = None
        self._user: List[UserAllocation] = []
        self._group: List[GroupAllocation] = []
        self._percentile: List[PercentileAllocation] = []
        self._seed = "allocation\n" + feature_name

    @classmethod
    def convert_from_json(cls, json: Dict[str, Any], feature_name: str) -> Optional["Allocation"]:
        """
        Convert a JSON object to Allocation.

        :param json: JSON object
        :type json: dict
        :return: Allocation
        :rtype: Allocation
        """
        if not json:
            return None
        allocation = cls(feature_name)
        allocation._default_when_enabled = json.get(DEFAULT_WHEN_ENABLED)
        allocation._default_when_disabled = json.get(DEFAULT_WHEN_DISABLED)
        allocation._user = []
        allocation._group = []
        allocation._percentile = []

        allocations: List[Any] = []
        if USER in json:
            allocations = cast(List[Any], json.get(USER, []))
            for user_allocation in allocations:
                allocation._user.append(UserAllocation(**user_allocation))
        if GROUP in json:
            allocations = cast(List[Any], json.get(GROUP, []))
            for group_allocation in allocations:
                allocation._group.append(GroupAllocation(**group_allocation))
        if PERCENTILE in json:
            allocations = cast(List[Any], json.get(PERCENTILE, []))
            for percentile_allocation in allocations:
                allocation._percentile.append(PercentileAllocation.convert_from_json(percentile_allocation))
        allocation._seed = json.get(SEED, allocation._seed)
        return allocation

    @property
    def default_when_enabled(self) -> Optional[str]:
        """
        Get the default variant when the feature flag is enabled.

        :return: Default variant when the feature flag is enabled.
        :rtype: str
        """
        return self._default_when_enabled

    @property
    def default_when_disabled(self) -> Optional[str]:
        """
        Get the default variant when the feature flag is disabled.

        :return: Default variant when the feature flag is disabled.
        :rtype: str
        """
        return self._default_when_disabled

    @property
    def user(self) -> List[UserAllocation]:
        """
        Get the user allocations.

        :return: User allocations.
        :rtype: list[UserAllocation]
        """
        return self._user

    @property
    def group(self) -> List[GroupAllocation]:
        """
        Get the group allocations.

        :return: Group allocations.
        :rtype: list[GroupAllocation]
        """
        return self._group

    @property
    def percentile(self) -> List[PercentileAllocation]:
        """
        Get the percentile allocations.

        :return: Percentile allocations.
        :rtype: list[PercentileAllocation]
        """
        return self._percentile

    @property
    def seed(self) -> str:
        """
        Get the seed for the allocation.

        :return: Seed for the allocation.
        :rtype: str
        """
        return self._seed
