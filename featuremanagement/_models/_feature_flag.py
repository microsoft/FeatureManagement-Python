# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from collections.abc import Mapping

FEATURE_FLAG_ID = "id"
FEATURE_FLAG_ENABLED = "enabled"
FEATURE_FLAG_CONDITIONS = "conditions"
FEATURE_FLAG_CLIENT_FILTERS = "client_filters"
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

    def _validate(self):
        if not isinstance(self._id, str):
            raise ValueError("Feature flag id field must be a string.")
        if not isinstance(self._enabled, bool):
            raise ValueError(f"Feature flag {self._id} must be a boolean.")
        self._conditions._validate(self._id)  # pylint: disable=protected-access


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
