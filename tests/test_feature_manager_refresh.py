# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import pytest
from featuremanagement import FeatureManager
from featuremanagement.aio import FeatureManager as AsyncFeatureManager


class TestFeatureManagerRefresh:
    # method: feature_manager_creation
    def test_refresh(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None
        assert feature_manager.is_enabled("Alpha")
        assert "Alpha" in feature_manager._cache  # pylint: disable=protected-access
        assert feature_manager.is_enabled("Alpha")  # test cache
        assert "Alpha" in feature_manager._cache  # pylint: disable=protected-access

        feature_flags["feature_management"] = {
            "feature_flags": [
                {"id": "Alpha", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
            ]
        }

        assert not feature_manager.is_enabled("Beta")  # resets cache
        assert "Alpha" not in feature_manager._cache  # pylint: disable=protected-access
        assert not feature_manager.is_enabled("Alpha")
        assert "Alpha" in feature_manager._cache  # pylint: disable=protected-access

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_refresh_async(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = AsyncFeatureManager(feature_flags)
        assert feature_manager is not None
        assert await feature_manager.is_enabled("Alpha")
        assert "Alpha" in feature_manager._cache  # pylint: disable=protected-access
        assert await feature_manager.is_enabled("Alpha")  # test cache
        assert "Alpha" in feature_manager._cache  # pylint: disable=protected-access

        feature_flags["feature_management"] = {
            "feature_flags": [
                {"id": "Alpha", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
            ]
        }

        assert not await feature_manager.is_enabled("Beta")  # resets cache
        assert "Alpha" not in feature_manager._cache  # pylint: disable=protected-access
        assert not await feature_manager.is_enabled("Alpha")
        assert "Alpha" in feature_manager._cache  # pylint: disable=protected-access
