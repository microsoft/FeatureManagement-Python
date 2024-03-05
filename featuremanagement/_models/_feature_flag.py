# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass

FEATURE_FLAG_ID = "id"
FEATURE_FLAG_ENABLED = "enabled"
FEATURE_FLAG_CONDITIONS = "conditions"
FEATURE_FLAG_CLIENT_FILTERS = "client_filters"
FEATURE_FLAG_ALLOCATION = "Allocation"
FEATURE_FLAG_VARIANTS = "Variants"
FEATURE_FILTER_NAME = "name"
FEATURE_FILTER_REQUIREMENT_TYPE = "requirement_type"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"


class FeatureConditions:

    @classmethod
    def convert_from_json(cls, json):
        if not json:
            return None
        conditions = cls()
        conditions.requirement_type = json.get(FEATURE_FILTER_REQUIREMENT_TYPE, REQUIREMENT_TYPE_ANY)
        conditions.client_filters = json.get(FEATURE_FLAG_CLIENT_FILTERS, [])
        return conditions
    
    def _validate(self, feature_flag_id):
        if self.requirement_type not in [REQUIREMENT_TYPE_ALL, REQUIREMENT_TYPE_ANY]:
            raise ValueError("Feature flag {} has invalid requirement type.".format(feature_flag_id))
        for feature_filter in self.client_filters:
            if feature_filter.get(FEATURE_FILTER_NAME) is None:
                raise ValueError("Feature flag {} is missing filter name.".format(feature_flag_id))

class FeatureFlag:
    @classmethod
    def convert_from_json(cls, jsonValue):
        feature_flag = cls()
        if not type(jsonValue) is dict:
            raise ValueError("Feature flag must be a dictionary.")
        feature_flag.id = jsonValue.get(FEATURE_FLAG_ID)
        feature_flag.enabled = _convert_boolean_value(jsonValue.get(FEATURE_FLAG_ENABLED, True))
        feature_flag.conditions = {}
        feature_flag.conditions = FeatureConditions.convert_from_json(jsonValue.get(FEATURE_FLAG_CONDITIONS, {}))
        feature_flag.allocation = Allocation.convert_from_json(jsonValue.get(FEATURE_FLAG_ALLOCATION, None))
        feature_flag.variants = None
        if FEATURE_FLAG_VARIANTS in jsonValue:
            variants = jsonValue.get(FEATURE_FLAG_VARIANTS)
            feature_flag.variants = []
            for variant in variants:
                feature_flag.variants.append(VariantReference.convert_from_json(variant))
        feature_flag._validate()
        return feature_flag

    @property
    def name(self):
        return self.id

    def _validate(self):
        if not isinstance(self.id, str):
            raise ValueError("Feature flag id field must be a string.")
        if not isinstance(self.enabled, bool):
            raise ValueError("Feature flag {} must be a boolean.".format(self.id))
        self.conditions._validate(self.id)

class Allocation:

    @classmethod
    def convert_from_json(cls, json):
        if not json:
            return None
        allocation = cls()
        allocation.default_when_enabled = json.get("default_when_enabled")
        allocation.default_when_disabled = json.get("default_when_disabled")
        allocation.users = []
        allocation.groups = []
        allocation.percentile = []
        if "users" in json:
            allocations = json.get("users")
            for user_allocation in allocations:
                allocation.users.append(UserAllocation(**user_allocation))
        if "groups" in json:
            allocations = json.get("groups")
            for group_allocation in allocations:
                allocation.groups.append(GroupAllocation(**group_allocation))
        if "percentile" in json:
            allocations = json.get("percentile")
            for percentile_allocation in allocations:
                allocation.percentile.append(PercentileAllocation.convert_from_json(**percentile_allocation))
        allocation.seed = json.get("seed")
        return allocation

@dataclass
class UserAllocation:

    variant: str
    users: dict

@dataclass
class GroupAllocation:

    variant: str
    groups: dict

class PercentileAllocation:

    @classmethod
    def convert_from_json(cls, json):
        if not json:
            return None
        user_allocation = cls()
        user_allocation.variant = json.get("variant")
        user_allocation.percentile_from = json.get("from")
        user_allocation.percentile_to = json.get("to")
        return user_allocation

@dataclass
class VariantReference:

    @classmethod
    def convert_from_json(cls, json):
        if not json:
            return None
        variant_reference = cls()
        variant_reference.name = json.get("name")
        variant_reference.configuration_value = json.get("configuration_value")
        variant_reference.configuration_reference = json.get("configuration_reference")
        variant_reference.status_override = _convert_boolean_value(json.get("status_override", None))
        return variant_reference


def _convert_boolean_value(enabled):
    if isinstance(enabled, bool):
        return enabled
    if enabled.lower() == "true":
        return True
    if enabled.lower() == "false":
        return False
    return enabled
