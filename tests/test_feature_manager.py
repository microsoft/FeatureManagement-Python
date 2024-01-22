# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from microsoft.featuremanagement import FeatureManager, FeatureFilter


class TestFeatureManagemer:
    # method: feature_manager_creation
    def test_empty_feature_manager_creation(self):
        feature_manager = FeatureManager({})
        assert feature_manager is not None
        assert not feature_manager.is_enabled("Alpha")

    # method: feature_manager_creation
    def test_basic_feature_manager_creation(self):
        feature_flags = {
            "FeatureManagement": {
                "FeatureFlags": [
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
            "FeatureManagement": {
                "FeatureFlags": [
                    {
                        "id": "Alpha",
                        "description": "",
                        "enabled": "true",
                        "conditions": {"client_filters": [{"name": "AllwaysOn", "parameters": {}}]},
                    },
                    {
                        "id": "Beta",
                        "description": "",
                        "enabled": "false",
                        "conditions": {"client_filters": [{"name": "AllwaysOn", "parameters": {}}]},
                    },
                    {
                        "id": "Gamma",
                        "description": "",
                        "enabled": "True",
                        "conditions": {"client_filters": [{"name": "AllwaysOff", "parameters": {}}]},
                    },
                    {
                        "id": "Delta",
                        "description": "",
                        "enabled": "False",
                        "conditions": {"client_filters": [{"name": "AllwaysOff", "parameters": {}}]},
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AllwaysOn(), AllwaysOff()])
        assert feature_manager is not None
        assert len(feature_manager._filters) == 4
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Beta")
        assert not feature_manager.is_enabled("Gamma")
        assert not feature_manager.is_enabled("Delta")
        assert not feature_manager.is_enabled("Epsilon")

    # method: feature_manager_creation
    def test_feature_manager_creation_with_filters(self):
        feature_manager = FeatureManager({}, feature_filters=[AllwaysOn(), AllwaysOff(), FakeTimeWindowFilter()])
        assert feature_manager is not None

        # The fake time window should override the default one
        assert len(feature_manager._filters) == 4


class AllwaysOn(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return True


class AllwaysOff(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return False


@FeatureFilter.alias("Microsoft.TimeWindow")
class FakeTimeWindowFilter(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return True
