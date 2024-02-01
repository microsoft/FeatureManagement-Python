# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import pytest
from microsoft.featuremanagement.aio import FeatureManager


class TestDefaultFeatureFlags:
    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_feature_manager_creation_with_targeting(self):
        feature_flags = {
            "FeatureManagement": {
                "FeatureFlags": [
                    {
                        "id": "Target",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.Targeting",
                                    "parameters": {
                                        "Audience": {
                                            "Users": ["Adam"],
                                            "Groups": [{"Name": "Stage1", "RolloutPercentage": 100}],
                                            "DefaultRolloutPercentage": 50,
                                            "Exclusion": {"Users": [], "Groups": []},
                                        }
                                    },
                                }
                            ]
                        },
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None
        # Adam is in the user audience
        assert await feature_manager.is_enabled("Target", user="Adam")
        # Brian is not part of the 50% or default 50% of users
        assert not await feature_manager.is_enabled("Target", user="Brian")
        # Brian is enabled because all of Stage 1 is enabled
        assert await feature_manager.is_enabled("Target", user="Brian", groups=["Stage1"])
        # Brian is not enabled because he is not in Stage 2, group isn't looked at when user is targeted
        assert not await feature_manager.is_enabled("Target", user="Brian", groups=["Stage2"])

    # method: feature_manager_creation
    @pytest.mark.asyncio
    async def test_feature_manager_creation_with_time_window(self):
        feature_flags = {
            "FeatureManagement": {
                "FeatureFlags": [
                    {
                        "id": "Alpha",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "Start": "Wed, 01 Jan 2020 00:00:00 GMT",
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "id": "Beta",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "End": "Sat, 01 Jan 3020 00:00:00 GMT",
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "id": "Gamma",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "End": "Wed, 01 Jan 2020 00:00:00 GMT",
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "id": "Delta",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "Start": "Sat, 01 Jan 3020 00:00:00 GMT",
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "id": "Epsilon",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "Start": "Wed, 01 Jan 2020 00:00:00 GMT",
                                        "End": "Sat, 01 Jan 3020 00:00:00 GMT",
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "id": "Foxtrot",
                        "enabled": "true",
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "Start": "Wed, 01 Jan 2020 00:00:00 GMT",
                                        "End": "Fri, 01 Jan 2021 00:00:00 GMT",
                                    },
                                }
                            ]
                        },
                    },
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None
        assert await feature_manager.is_enabled("Alpha")
        assert await feature_manager.is_enabled("Beta")
        assert not await feature_manager.is_enabled("Gamma")
        assert not await feature_manager.is_enabled("Delta")
        assert await feature_manager.is_enabled("Epsilon")
        assert not await feature_manager.is_enabled("Foxtrot")

    @pytest.mark.asyncio
    async def test_feature_manager_invalid_feature_flag(self):
        feature_flags = {
            "FeatureManagement": {
                "FeatureFlags": [
                    {},
                ]
            }
        }

        feature_manager = FeatureManager(feature_flags)
        assert not await feature_manager.is_enabled("Alpha")

        feature_flags["FeatureManagement"]["FeatureFlags"][0]["id"] = 1

        with pytest.raises(ValueError, match="Feature flag id field must be a string."):
            feature_manager = FeatureManager(feature_flags)
            await feature_manager.is_enabled(1)

        feature_flags["FeatureManagement"]["FeatureFlags"][0]["id"] = "featureFlagId"
        feature_flags["FeatureManagement"]["FeatureFlags"][0]["enabled"] = "true"

        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        feature_flags["FeatureManagement"]["FeatureFlags"][0]["conditions"] = {}
        feature_flags["FeatureManagement"]["FeatureFlags"][0]["conditions"]["client_filters"] = []

        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        feature_flags["FeatureManagement"]["FeatureFlags"][0]["conditions"]["client_filters"].append({})

        with pytest.raises(ValueError, match="Feature flag featureFlagId is missing filter name."):
            FeatureManager(feature_flags)
            await feature_manager.is_enabled("featureFlagId")
