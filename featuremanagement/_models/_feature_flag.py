# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from typing import cast, List, Union, Optional, Mapping, Any
from ._feature_conditions import FeatureConditions
from ._allocation import Allocation
from ._variant_reference import VariantReference
from ._telemetry import Telemetry
from ._constants import (
    FEATURE_FLAG_ID,
    FEATURE_FLAG_ENABLED,
    FEATURE_FLAG_CONDITIONS,
    FEATURE_FLAG_ALLOCATION,
    FEATURE_FLAG_VARIANTS,
)


class FeatureFlag:
    """
    Represents a feature flag.
    """

    def __init__(self) -> None:
        self._id: str = ""
        self._enabled = False
        self._conditions: FeatureConditions = FeatureConditions()
        self._allocation: Optional[Allocation] = None
        self._variants: Optional[List[VariantReference]] = None
        self._telemetry: Telemetry = Telemetry()

    @classmethod
    def convert_from_json(cls, json_value: Mapping[str, Any]) -> "FeatureFlag":
        """
        Convert a JSON object to FeatureFlag.

        :param dict json_value: JSON object
        :return: FeatureFlag.
        :rtype: FeatureFlag
        """
        feature_flag = cls()
        feature_flag._id = json_value.get(FEATURE_FLAG_ID, "")
        feature_flag._enabled = _convert_boolean_value(json_value.get(FEATURE_FLAG_ENABLED, False), feature_flag._id)
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
        if FEATURE_FLAG_VARIANTS in json_value:
            variants: List[Mapping[str, Any]] = json_value.get(FEATURE_FLAG_VARIANTS, [])
            feature_flag._variants = []
            for variant in variants:
                if variant:
                    feature_flag._variants.append(VariantReference.convert_from_json(variant))
        if "telemetry" in json_value:
            feature_flag._telemetry = Telemetry(**cast(Any, json_value.get("telemetry")))
        feature_flag._validate()
        return feature_flag

    @property
    def name(self) -> Optional[str]:
        """
        Get the name of the feature flag.

        :return: Name of the feature flag.
        :rtype: str
        """
        return self._id

    @property
    def enabled(self) -> bool:
        """
        Get the status of the feature flag.

        :return: Status of the feature flag.
        :rtype: bool
        """
        return self._enabled

    @property
    def conditions(self) -> FeatureConditions:
        """
        Get the conditions for the feature flag.

        :return: Conditions for the feature flag.
        :rtype: FeatureConditions
        """
        return self._conditions

    @property
    def allocation(self) -> Optional[Allocation]:
        """
        Get the allocation for the feature flag.

        :return: Allocation for the feature flag.
        :rtype: Allocation
        """
        return self._allocation

    @property
    def variants(self) -> Optional[List[VariantReference]]:
        """
        Get the variants for the feature flag.

        :return: Variants for the feature flag.
        :rtype: list[VariantReference]
        """
        return self._variants

    @property
    def telemetry(self) -> Telemetry:
        """
        Get the telemetry configuration for the feature flag.

        :return: Telemetry for the feature flag.
        :rtype: Telemetry
        """
        return self._telemetry

    def _validate(self) -> None:
        if not isinstance(self._id, str):
            raise ValueError(f"Invalid setting 'id' with value '{self._id}' for feature '{self._id}'.")
        if not isinstance(self._enabled, bool):
            raise ValueError(f"Invalid setting 'enabled' with value '{self._enabled}' for feature '{self._id}'.")
        self.conditions._validate(self._id)  # pylint: disable=protected-access


def _convert_boolean_value(enabled: Union[str, bool], feature_name: str) -> bool:
    """
    Convert the value to a boolean if it is a string.

    :param Union[str, bool] enabled: Value to be converted.
    :return: Converted value.
    :rtype: bool
    """
    if isinstance(enabled, bool):
        return enabled
    if enabled.lower() == "true":
        return True
    if enabled.lower() == "false":
        return False
    raise ValueError(f"Invalid setting 'enabled' with value '{enabled}' for feature '{feature_name}'.")
