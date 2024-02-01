# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

FEATURE_FLAG_ID = "id"
FEATURE_FLAG_ENABLED = "enabled"
FEATURE_FLAG_CONDITIONS = "conditions"
FEATURE_FLAG_CLIENT_FILTERS = "client_filters"
FEATURE_FILTER_NAME = "name"
FEATURE_FILTER_REQUIREMENT_TYPE = "requirement_type"
REQUIREMENT_TYPE_ALL = "All"
REQUIREMENT_TYPE_ANY = "Any"


class FeatureConditions:
    @classmethod
    def convert_from_json(cls, json):
        conditions = cls()
        conditions._requirement_type = json.get(FEATURE_FILTER_REQUIREMENT_TYPE, REQUIREMENT_TYPE_ANY)
        conditions._client_filters = json.get(FEATURE_FLAG_CLIENT_FILTERS, [])
        return conditions

    @property
    def requirement_type(self):
        return self._requirement_type

    @property
    def client_filters(self):
        return self._client_filters

    def _validate(self, feature_flag_id):
        if self._requirement_type not in [REQUIREMENT_TYPE_ALL, REQUIREMENT_TYPE_ANY]:
            raise ValueError("Feature flag {} has invalid requirement type.".format(feature_flag_id))
        for feature_filter in self._client_filters:
            if feature_filter.get(FEATURE_FILTER_NAME) is None:
                raise ValueError("Feature flag {} is missing filter name.".format(feature_flag_id))

    def __repr__(self):
        return "<FeatureConditions requirement_type={} client_filters={}>".format(
            self._requirement_type, self._client_filters
        )


class FeatureFlag:
    @classmethod
    def convert_from_json(cls, jsonValue):
        feature_flag = cls()
        if (not type(jsonValue) is dict):
            raise ValueError("Feature flag must be a dictionary.")
        feature_flag._id = jsonValue.get(FEATURE_FLAG_ID)
        feature_flag._enabled = _convert_boolean_value(jsonValue.get(FEATURE_FLAG_ENABLED, True))
        feature_flag._conditions = FeatureConditions.convert_from_json(jsonValue.get(FEATURE_FLAG_CONDITIONS, {}))
        feature_flag._validate()
        return feature_flag

    @property
    def name(self):
        return self._id

    @property
    def enabled(self):
        return self._enabled

    @property
    def conditions(self):
        return self._conditions

    def _validate(self):
        if not isinstance(self._id, str):
            raise ValueError("Feature flag id field must be a string.")
        if not isinstance(self._enabled, bool):
            raise ValueError("Feature flag {} must be a boolean.".format(self._id))
        self._conditions._validate(self._id)

    def __repr__(self):
        return "<FeatureFlag name={} enabled={} conditions={}>".format(self._id, self._enabled, self._conditions)


def _convert_boolean_value(enabled):
    if isinstance(enabled, bool):
        return enabled
    if enabled.lower() == "true":
        return True
    if enabled.lower() == "false":
        return False
    return enabled
