# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass
from collections.abc import Mapping

FEATURE_FLAG_ID = "id"
FEATURE_FLAG_ENABLED = "enabled"
FEATURE_FLAG_CONDITIONS = "conditions"
FEATURE_FLAG_CLIENT_FILTERS = "client_filters"
FEATURE_FLAG_ALLOCATION = "allocation"
FEATURE_FLAG_VARIANTS = "variants"
FEATURE_FILTER_NAME = "name"
FEATURE_FILTER_REQUIREMENT_TYPE = "requirement_type"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"


class FeatureConditions:
    """
    Represents the conditions for a feature flag
    """

    def __init__(self):
        self._requirement_type = REQUIREMENT_TYPE_ANY
        self._client_filters = []

    @classmethod
    def convert_from_json(cls, feature_name, json_value):
        """
        Convert a JSON object to FeatureConditions

        :param json: JSON object
        :type json: dict
        :return: FeatureConditions
        :rtype: FeatureConditions
        """
        conditions = cls()
        if json_value is not None and not isinstance(json_value, Mapping):
            raise AttributeError("Feature flag conditions must be a dictionary")
        conditions._requirement_type = json_value.get(FEATURE_FILTER_REQUIREMENT_TYPE, REQUIREMENT_TYPE_ANY)
        conditions._client_filters = json_value.get(FEATURE_FLAG_CLIENT_FILTERS, [])
        for feature_filter in conditions._client_filters:
            feature_filter["feature_name"] = feature_name
        return conditions

    @property
    def requirement_type(self):
        """
        Get the requirement type for the feature flag

        :return: Requirement type
        :rtype: str
        """
        return self._requirement_type

    @property
    def client_filters(self):
        """
        Get the client filters for the feature flag

        :return: Client filters
        :rtype: list[dict]
        """
        return self._client_filters

    def _validate(self, feature_flag_id):
        if self._requirement_type not in [REQUIREMENT_TYPE_ALL, REQUIREMENT_TYPE_ANY]:
            raise ValueError(f"Feature flag {feature_flag_id} has invalid requirement type.")
        for feature_filter in self._client_filters:
            if feature_filter.get(FEATURE_FILTER_NAME) is None:
                raise ValueError(f"Feature flag {feature_flag_id} is missing filter name.")


class FeatureFlag:
    """
    Represents a feature flag
    """

    def __init__(self):
        self._id = None
        self._enabled = False
        self._conditions = FeatureConditions()
        self._allocation = None
        self._variants = None

    @classmethod
    def convert_from_json(cls, json_value):
        """
        Convert a JSON object to FeatureFlag

        :param json_value: JSON object
        :type json_value: dict
        :return: FeatureFlag
        :rtype: FeatureFlag
        """
        feature_flag = cls()
        if not isinstance(json_value, dict):
            raise ValueError("Feature flag must be a dictionary.")
        feature_flag._id = json_value.get(FEATURE_FLAG_ID)
        feature_flag._enabled = _convert_boolean_value(json_value.get(FEATURE_FLAG_ENABLED, True))
        feature_flag._conditions = FeatureConditions.convert_from_json(
            feature_flag._id, json_value.get(FEATURE_FLAG_CONDITIONS, {})
        )
        if FEATURE_FLAG_CONDITIONS in json_value:
            feature_flag._conditions = FeatureConditions.convert_from_json(
                feature_flag._id, json_value.get(FEATURE_FLAG_CONDITIONS, {})
            )
        else:
            feature_flag._conditions = FeatureConditions()
        feature_flag._allocation = Allocation.convert_from_json(json_value.get(FEATURE_FLAG_ALLOCATION, None))
        feature_flag._variants = None
        if FEATURE_FLAG_VARIANTS in json_value:
            variants = json_value.get(FEATURE_FLAG_VARIANTS)
            feature_flag._variants = []
            for variant in variants:
                feature_flag._variants.append(VariantReference.convert_from_json(variant))
        feature_flag._validate()
        return feature_flag

    @property
    def name(self):
        """
        Get the name of the feature flag

        :return: Name of the feature flag
        :rtype: str
        """
        return self._id

    @property
    def enabled(self):
        """
        Get the status of the feature flag

        :return: Status of the feature flag
        :rtype: bool
        """
        return self._enabled

    @property
    def conditions(self):
        """
        Get the conditions for the feature flag

        :return: Conditions for the feature flag
        :rtype: FeatureConditions
        """
        return self._conditions

    @property
    def allocation(self):
        """
        Get the allocation for the feature flag

        :return: Allocation for the feature flag
        :rtype: Allocation
        """
        return self._allocation

    @property
    def variants(self):
        """
        Get the variants for the feature flag

        :return: Variants for the feature flag
        :rtype: list[VariantReference]
        """
        return self._variants

    def _validate(self):
        if not isinstance(self._id, str):
            raise ValueError("Feature flag id field must be a string.")
        if not isinstance(self._enabled, bool):
            raise ValueError(f"Feature flag {self._id} must be a boolean.")
        self.conditions._validate(self._id)  # pylint: disable=protected-access


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
        allocation._default_when_enabled = json.get("default_when_enabled")
        allocation._default_when_disabled = json.get("default_when_disabled")
        allocation._user = []
        allocation._group = []
        allocation._percentile = []
        if "user" in json:
            allocations = json.get("user")
            for user_allocation in allocations:
                allocation._user.append(UserAllocation(**user_allocation))
        if "group" in json:
            allocations = json.get("group")
            for group_allocation in allocations:
                allocation._group.append(GroupAllocation(**group_allocation))
        if "percentile" in json:
            allocations = json.get("percentile")
            for percentile_allocation in allocations:
                allocation._percentile.append(PercentileAllocation.convert_from_json(percentile_allocation))
        allocation._seed = json.get("seed", "")
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


@dataclass
class VariantReference:
    """
    Represents a variant reference
    """

    def __init__(self):
        self._name = None
        self._configuration_value = None
        self._configuration_reference = None
        self._status_override = None

    @classmethod
    def convert_from_json(cls, json):
        """
        Convert a JSON object to VariantReference

        :param json: JSON object
        :type json: dict
        :return: VariantReference
        :rtype: VariantReference
        """
        if not json:
            return None
        variant_reference = cls()
        variant_reference._name = json.get("name")
        variant_reference._configuration_value = json.get("configuration_value")
        variant_reference._configuration_reference = json.get("configuration_reference")
        variant_reference._status_override = json.get("status_override", None)
        return variant_reference

    @property
    def name(self):
        """
        Get the name of the variant

        :return: Name of the variant
        :rtype: str
        """
        return self._name

    @property
    def configuration_value(self):
        """
        Get the configuration value for the variant

        :return: Configuration value for the variant
        :rtype: str
        """
        return self._configuration_value

    @property
    def configuration_reference(self):
        """
        Get the configuration reference for the variant

        :return: Configuration reference for the variant
        :rtype: str
        """
        return self._configuration_reference

    @property
    def status_override(self):
        """
        Get the status override for the variant

        :return: Status override for the variant
        :rtype: str
        """
        return self._status_override


def _convert_boolean_value(enabled):
    """
    Convert the value to a boolean if it is a string

    :param enabled: Value to be converted
    :type enabled: str or bool
    :return: Converted value
    :rtype: bool
    """
    if isinstance(enabled, bool):
        return enabled
    if enabled.lower() == "true":
        return True
    if enabled.lower() == "false":
        return False
    return enabled
