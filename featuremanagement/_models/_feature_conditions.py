# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from collections.abc import Mapping
from typing import Any, Dict, List
from ._constants import (
    FEATURE_FLAG_CLIENT_FILTERS,
    FEATURE_FILTER_NAME,
    FEATURE_FILTER_REQUIREMENT_TYPE,
    REQUIREMENT_TYPE_ALL,
    REQUIREMENT_TYPE_ANY,
)


class FeatureConditions:
    """
    Represents the conditions for a feature flag.
    """

    def __init__(self) -> None:
        self._requirement_type = REQUIREMENT_TYPE_ANY
        self._client_filters: List[Dict[str, Any]] = []

    @classmethod
    def convert_from_json(cls, feature_name: str, json_value: str) -> "FeatureConditions":
        """
        Convert a JSON object to FeatureConditions.

        :param dict json: JSON object.
        :return: FeatureConditions.
        :rtype: FeatureConditions
        """
        conditions = cls()
        if json_value is not None and not isinstance(json_value, Mapping):
            raise AttributeError("Feature flag conditions must be a dictionary")
        conditions._requirement_type = json_value.get(FEATURE_FILTER_REQUIREMENT_TYPE, REQUIREMENT_TYPE_ANY)
        conditions._client_filters = json_value.get(FEATURE_FLAG_CLIENT_FILTERS, [])
        if not isinstance(conditions._client_filters, list):
            conditions._client_filters = []
        for feature_filter in conditions._client_filters:
            feature_filter["feature_name"] = feature_name
        return conditions

    @property
    def requirement_type(self) -> str:
        """
        Get the requirement type for the feature flag.

        :return: Requirement type.
        :rtype: str
        """
        return self._requirement_type

    @property
    def client_filters(self) -> List[Dict[str, Any]]:
        """
        Get the client filters for the feature flag.

        :return: Client filters.
        :rtype: list[dict]
        """
        return self._client_filters

    def _validate(self, feature_flag_id: str) -> None:
        if self._requirement_type not in [REQUIREMENT_TYPE_ALL, REQUIREMENT_TYPE_ANY]:
            raise ValueError(f"Feature flag {feature_flag_id} has invalid requirement type.")
        for feature_filter in self._client_filters:
            if feature_filter.get(FEATURE_FILTER_NAME) is None:
                raise ValueError(f"Feature flag {feature_flag_id} is missing filter name.")
