# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from ._feature_conditions import FeatureConditions
from ._constants import (
    FEATURE_FLAG_ID,
    FEATURE_FLAG_ENABLED,
    FEATURE_FLAG_CONDITIONS,
)


class FeatureFlag:
    """
    Represents a feature flag.
    """

    def __init__(self):
        self._id = None
        self._enabled = False
        self._conditions = FeatureConditions()

    @classmethod
    def convert_from_json(cls, json_value):
        """
        Convert a JSON object to FeatureFlag.

        :param dict json_value: JSON object
        :return: FeatureFlag.
        :rtype: FeatureFlag
        """
        feature_flag = cls()
        if not isinstance(json_value, dict):
            raise ValueError("Feature flag must be a dictionary.")
        feature_flag._id = json_value.get(FEATURE_FLAG_ID)
        feature_flag._enabled = _convert_boolean_value(json_value.get(FEATURE_FLAG_ENABLED, False))
        feature_flag._conditions = FeatureConditions.convert_from_json(
            feature_flag._id, json_value.get(FEATURE_FLAG_CONDITIONS, {})
        )
        if FEATURE_FLAG_CONDITIONS in json_value:
            feature_flag._conditions = FeatureConditions.convert_from_json(
                feature_flag._id, json_value.get(FEATURE_FLAG_CONDITIONS, {})
            )
        else:
            feature_flag._conditions = FeatureConditions()
        feature_flag._validate()
        return feature_flag

    @property
    def name(self):
        """
        Get the name of the feature flag.

        :return: Name of the feature flag.
        :rtype: str
        """
        return self._id

    @property
    def enabled(self):
        """
        Get the status of the feature flag.

        :return: Status of the feature flag.
        :rtype: bool
        """
        return self._enabled

    @property
    def conditions(self):
        """
        Get the conditions for the feature flag.

        :return: Conditions for the feature flag.
        :rtype: FeatureConditions
        """
        return self._conditions

    def _validate(self):
        if not isinstance(self._id, str):
            raise ValueError(f"Invalid setting 'id' with value '{self._id}' for feature '{self._id}'.")
        if not isinstance(self._enabled, bool):
            raise ValueError(f"Invalid setting 'enabled' with value '{self._enabled}' for feature '{self._id}'.")
        self.conditions._validate(self._id)  # pylint: disable=protected-access


def _convert_boolean_value(enabled):
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
    return enabled
