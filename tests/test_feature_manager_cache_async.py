# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement.aio import FeatureManager
import pytest


class TestFeatureManagemer:
    # method: is_enabled
    @pytest.mark.asyncio
    async def test_cache(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {"id": "Alpha", "description": "", "enabled": "true", "conditions": {"client_filters": []}},
                    {"id": "Beta", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert await feature_manager.is_enabled("Alpha")
        assert await feature_manager.is_enabled("Alpha")  # test cache

        feature_flags["feature_management"] = {
            "feature_flags": [
                {"id": "Alpha", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
                {"id": "Beta", "description": "", "enabled": "false", "conditions": {"client_filters": []}},
            ]
        }
        assert not await feature_manager.is_enabled("Alpha")  # test cache
