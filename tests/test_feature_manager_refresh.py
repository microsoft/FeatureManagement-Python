# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import pytest
from microsoft.featuremanagement import FeatureManager
from microsoft.featuremanagement.aio import FeatureManager as AsyncFeatureManager


class TestFeatureManagemerRefresh:

    # method: feature_manager_creation
    def test_refresh(self):
        feature_flags = {
            "FeatureManagement": {
                "FeatureFlags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None
        assert feature_manager.is_enabled("Alpha")

        feature_flags.get("FeatureManagement").get("FeatureFlags")[0]["enabled"] = "false"

        assert not feature_manager.is_enabled("Alpha")

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_refresh_async(self):
        feature_flags = {
            "FeatureManagement": {
                "FeatureFlags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = AsyncFeatureManager(feature_flags)
        assert feature_manager is not None
        assert await feature_manager.is_enabled("Alpha")

        feature_flags.get("FeatureManagement").get("FeatureFlags")[0]["enabled"] = "false"

        assert not await feature_manager.is_enabled("Alpha")
