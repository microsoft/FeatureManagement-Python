# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from ._feature_conditions import FeatureConditions
from ._allocation import Allocation
from ._variant_reference import VariantReference
from ._constants import (
    FEATURE_FLAG_ID,
    FEATURE_FLAG_ENABLED,
    FEATURE_FLAG_CONDITIONS,
    FEATURE_FLAG_ALLOCATION,
    FEATURE_FLAG_VARIANTS,
)


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
        feature_flag._allocation = Allocation.convert_from_json(
            json_value.get(FEATURE_FLAG_ALLOCATION, None), feature_flag._id
        )
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
