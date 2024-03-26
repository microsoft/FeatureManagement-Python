# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass
from ._constants import DEFAULT_WHEN_ENABLED, DEFAULT_WHEN_DISABLED, USER, GROUP, PERCENTILE, SEED


class Allocation:
    """
    Represents an allocation
    """

    def __init__(self):
        self._default_when_enabled = None
        self._default_when_disabled = None
        self._user = []
        self._group = []
        self._percentile = []
        self._seed = None

    @classmethod
    def convert_from_json(cls, json):
        """
        Convert a JSON object to Allocation

        :param json: JSON object
        :type json: dict
        :return: Allocation
        :rtype: Allocation
        """
        if not json:
            return None
        allocation = cls()
        allocation._default_when_enabled = json.get(DEFAULT_WHEN_ENABLED)
        allocation._default_when_disabled = json.get(DEFAULT_WHEN_DISABLED)
        allocation._user = []
        allocation._group = []
        allocation._percentile = []
        if USER in json:
            allocations = json.get(USER)
            for user_allocation in allocations:
                allocation._user.append(UserAllocation(**user_allocation))
        if GROUP in json:
            allocations = json.get(GROUP)
            for group_allocation in allocations:
                allocation._group.append(GroupAllocation(**group_allocation))
        if PERCENTILE in json:
            allocations = json.get(PERCENTILE)
            for percentile_allocation in allocations:
                allocation._percentile.append(PercentileAllocation.convert_from_json(percentile_allocation))
        allocation._seed = json.get(SEED, "")
        return allocation

    @property
    def default_when_enabled(self):
        """
        Get the default variant when the feature flag is enabled

        :return: Default variant when the feature flag is enabled
        :rtype: str
        """
        return self._default_when_enabled

    @property
    def default_when_disabled(self):
        """
        Get the default variant when the feature flag is disabled

        :return: Default variant when the feature flag is disabled
        :rtype: str
        """
        return self._default_when_disabled

    @property
    def user(self):
        """
        Get the user allocations

        :return: User allocations
        :rtype: list[UserAllocation]
        """
        return self._user

    @property
    def group(self):
        """
        Get the group allocations

        :return: Group allocations
        :rtype: list[GroupAllocation]
        """
        return self._group

    @property
    def percentile(self):
        """
        Get the percentile allocations

        :return: Percentile allocations
        :rtype: list[PercentileAllocation]
        """
        return self._percentile

    @property
    def seed(self):
        """
        Get the seed for the allocation

        :return: Seed for the allocation
        :rtype: str
        """
        return self._seed


@dataclass
class UserAllocation:
    """
    Represents a user allocation
    """

    variant: str
    users: list


@dataclass
class GroupAllocation:
    """
    Represents a group allocation
    """

    variant: str
    groups: list


class PercentileAllocation:
    """
    Represents a percentile allocation
    """

    def __init__(self):
        self._variant = None
        self._percentile_from = None
        self._percentile_to = None

    @classmethod
    def convert_from_json(cls, json):
        """
        Convert a JSON object to PercentileAllocation

        :param json: JSON object
        :type json: dict
        :return: PercentileAllocation
        :rtype: PercentileAllocation
        """
        if not json:
            return None
        user_allocation = cls()
        user_allocation._variant = json.get("variant")
        user_allocation._percentile_from = json.get("from")
        user_allocation._percentile_to = json.get("to")
        return user_allocation

    @property
    def variant(self):
        """
        Get the variant for the allocation

        :return: Variant for the allocation
        :rtype: str
        """
        return self._variant

    @property
    def percentile_from(self):
        """
        Get the starting percentile for the allocation

        :return: Starting percentile for the allocation
        :rtype: int
        """
        return self._percentile_from

    @property
    def percentile_to(self):
        """
        Get the ending percentile for the allocation

        :return: Ending percentile for the allocation
        :rtype: int
        """
        return self._percentile_to
