# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import unittest
import pytest
from featuremanagement.aio import FeatureManager, FeatureFilter


class TestFeatureManager(unittest.IsolatedAsyncioTestCase):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName=methodName)
        self.called_telemetry = False

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_empty_feature_manager_creation(self):
        feature_manager = FeatureManager({})
        assert feature_manager is not None
        assert not await feature_manager.is_enabled("Alpha")

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_basic_feature_manager_creation(self):
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
        assert await feature_manager.is_enabled("Alpha")
        assert not await feature_manager.is_enabled("Beta")

    # method: feature_manager_creation
    @pytest.mark.asyncio
    def test_feature_manager_creation_invalid_feature_filter(self):
        feature_flags = {"feature_management": {"feature_flags": []}}
        with self.assertRaises(ValueError):
            FeatureManager(feature_flags, feature_filters=["invalid_filter"])

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_feature_manager_creation_with_filters(self):
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
        assert await feature_manager.is_enabled("Alpha")
        assert not await feature_manager.is_enabled("Beta")
        assert not await feature_manager.is_enabled("Gamma")
        assert not await feature_manager.is_enabled("Delta")
        assert not await feature_manager.is_enabled("Epsilon")

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_feature_manager_creation_with_override_default(self):
        feature_manager = FeatureManager({}, feature_filters=[AlwaysOn(), AlwaysOff(), FakeTimeWindowFilter()])
        assert feature_manager is not None

        # The fake time window should override the default one
        assert len(feature_manager._filters) == 4  # pylint: disable=protected-access

    # method: list_feature_flags
    @pytest.mark.asyncio
    async def test_list_feature_flags(self):
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
        assert await feature_manager.is_enabled("Alpha")
        assert not await feature_manager.is_enabled("Beta")
        assert len(feature_manager.list_feature_flag_names()) == 2

    # method: is_enabled
    @pytest.mark.asyncio
    async def test_unknown_feature_filter(self):
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
            await feature_manager.is_enabled("Alpha")
        assert e_info.type == ValueError
        assert e_info.value.args[0] == "Feature flag Alpha has unknown filter UnknownFilter"

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_feature_with_telemetry(self):
        self.called_telemetry = False
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "telemetry": {"enabled": "true"}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, on_feature_evaluated=self.fake_telemetry_callback)
        assert feature_manager is not None
        assert await feature_manager.is_enabled("Alpha")
        assert self.called_telemetry

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_feature_with_telemetry_async(self):
        self.called_telemetry = False
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "telemetry": {"enabled": "true"}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, on_feature_evaluated=self.fake_telemetry_callback_async)
        assert feature_manager is not None
        assert await feature_manager.is_enabled("Alpha")
        assert self.called_telemetry

    def fake_telemetry_callback(self, evaluation_event):
        assert evaluation_event
        self.called_telemetry = True

    async def fake_telemetry_callback_async(self, evaluation_event):
        assert evaluation_event
        self.called_telemetry = True

    # method: duplicate_feature_flag_handling
    @pytest.mark.asyncio
    async def test_duplicate_feature_flags_last_wins_async(self):
        """Test that when multiple feature flags have the same ID, the last one wins."""
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "DuplicateFlag",
                        "description": "First",
                        "enabled": "true",
                        "conditions": {"client_filters": []},
                    },
                    {
                        "id": "DuplicateFlag",
                        "description": "Second",
                        "enabled": "false",
                        "conditions": {"client_filters": []},
                    },
                    {
                        "id": "DuplicateFlag",
                        "description": "Third",
                        "enabled": "true",
                        "conditions": {"client_filters": []},
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)

        # The last flag should win (enabled: true)
        assert await feature_manager.is_enabled("DuplicateFlag") == True

        # Should only list unique names
        flag_names = feature_manager.list_feature_flag_names()
        assert "DuplicateFlag" in flag_names
        # Count how many times DuplicateFlag appears in the list
        duplicate_count = flag_names.count("DuplicateFlag")
        assert duplicate_count == 1, f"Expected DuplicateFlag to appear once, but appeared {duplicate_count} times"

    @pytest.mark.asyncio
    async def test_duplicate_feature_flags_last_wins_disabled_async(self):
        """Test that when multiple feature flags have the same ID, the last one wins even if disabled."""
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "DuplicateFlag",
                        "description": "First",
                        "enabled": "true",
                        "conditions": {"client_filters": []},
                    },
                    {
                        "id": "DuplicateFlag",
                        "description": "Second",
                        "enabled": "true",
                        "conditions": {"client_filters": []},
                    },
                    {
                        "id": "DuplicateFlag",
                        "description": "Third",
                        "enabled": "false",
                        "conditions": {"client_filters": []},
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)

        # The last flag should win (enabled: false)
        assert await feature_manager.is_enabled("DuplicateFlag") == False


class AlwaysOn(FeatureFilter):
    async def evaluate(self, context, **kwargs):
        return True


class AlwaysOff(FeatureFilter):
    async def evaluate(self, context, **kwargs):
        return False


@FeatureFilter.alias("Microsoft.TimeWindow")
class FakeTimeWindowFilter(FeatureFilter):
    async def evaluate(self, context, **kwargs):
        return True
