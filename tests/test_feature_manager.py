# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import pytest
from featuremanagement import FeatureManager, FeatureFilter


class TestFeatureManager:
    # method: feature_manager_creation
    def test_empty_feature_manager_creation(self):
        feature_manager = FeatureManager({})
        assert feature_manager is not None
        assert not feature_manager.is_enabled("Alpha")

    # method: feature_manager_creation
    def test_basic_feature_manager_creation(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                    {"id": "Beta", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Beta")

    # method: feature_manager_creation
    def test_feature_manager_creation_with_filters(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "description": "",
                        "enabled": "true",
                        "conditions": {"client_filters": [{"name": "AlwaysOn", "parameters": {}}]},
                    },
                    {
                        "id": "Beta",
                        "description": "",
                        "enabled": "false",
                        "conditions": {"client_filters": [{"name": "AlwaysOn", "parameters": {}}]},
                    },
                    {
                        "id": "Gamma",
                        "description": "",
                        "enabled": "True",
                        "conditions": {"client_filters": [{"name": "AlwaysOff", "parameters": {}}]},
                    },
                    {
                        "id": "Delta",
                        "description": "",
                        "enabled": "False",
                        "conditions": {"client_filters": [{"name": "AlwaysOff", "parameters": {}}]},
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOn(), AlwaysOff()])
        assert feature_manager is not None
        assert len(feature_manager._filters) == 4  # pylint: disable=protected-access
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Beta")
        assert not feature_manager.is_enabled("Gamma")
        assert not feature_manager.is_enabled("Delta")
        assert not feature_manager.is_enabled("Epsilon")

    # method: feature_manager_creation
    def test_feature_manager_creation_with_override_default(self):
        feature_manager = FeatureManager({}, feature_filters=[AlwaysOn(), AlwaysOff(), FakeTimeWindowFilter()])
        assert feature_manager is not None

        # The fake time window should override the default one
        assert len(feature_manager._filters) == 4  # pylint: disable=protected-access

    # method: list_feature_flags
    def test_list_feature_flags(self):
        feature_manager = FeatureManager({})
        assert feature_manager is not None
        assert len(feature_manager.list_feature_flag_names()) == 0

        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                    {"id": "Beta", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Beta")
        assert len(feature_manager.list_feature_flag_names()) == 2

    # method: is_enabled
    def test_unknown_feature_filter(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "description": "",
                        "enabled": "true",
                        "conditions": {"client_filters": [{"name": "UnknownFilter", "parameters": {}}]},
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOn(), AlwaysOff()])
        assert feature_manager is not None
        with pytest.raises(ValueError) as e_info:
            feature_manager.is_enabled("Alpha")
        assert e_info.type == ValueError
        assert e_info.value.args[0] == "Feature flag Alpha has unknown filter UnknownFilter"


class AlwaysOn(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return True


class AlwaysOff(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return False


@FeatureFilter.alias("Microsoft.TimeWindow")
class FakeTimeWindowFilter(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return True
