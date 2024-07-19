# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from unittest import IsolatedAsyncioTestCase
from featuremanagement.aio import FeatureManager, FeatureFilter
from featuremanagement import TargetingContext


class TestFeatureVariantsAsync(IsolatedAsyncioTestCase):
    # method: is_enabled
    async def test_basic_feature_variant_override_enabled(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": True,
                        "variants": [
                            {"name": "On", "status_override": "Disabled"},
                        ],
                        "allocation": {
                            "default_when_enabled": "On",
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert not await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")).name == "On"

    # method: is_enabled
    async def test_basic_feature_variant_override_disabled(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": False,
                        "variants": [
                            {"name": "Off", "status_override": "Enabled"},
                        ],
                        "allocation": {
                            "default_when_disabled": "Off",
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)

        # Enabled = False takes precedence over status_override
        assert not await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")).name == "Off"

    # method: is_enabled
    async def test_basic_feature_variant_no_override(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": False,
                        "variants": [
                            {"name": "Off"},
                        ],
                        "allocation": {
                            "default_when_disabled": "Off",
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags)
        assert not await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")).name == "Off"

    # method: is_enabled
    async def test_basic_feature_variant_allocation_users(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": True,
                        "variants": [
                            {"name": "Off", "status_override": "Enabled"},
                            {"name": "On", "status_override": "Disabled"},
                        ],
                        "allocation": {
                            "user": [{"variant": "On", "users": ["Adam"]}, {"variant": "Off", "users": ["Brittney"]}],
                        },
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "AlwaysOnFilter",
                                    "parameters": {},
                                }
                            ]
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOnFilter()])
        assert await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")) is None
        assert not await feature_manager.is_enabled("Alpha", "Adam")
        assert (await feature_manager.get_variant("Alpha", "Adam")).name == "On"
        assert await feature_manager.is_enabled("Alpha", "Brittney")
        assert (await feature_manager.get_variant("Alpha", "Brittney")).name == "Off"
        assert await feature_manager.is_enabled("Alpha", "Charlie")
        assert (await feature_manager.get_variant("Alpha", "Charlie")) is None

    # method: is_enabled
    async def test_basic_feature_variant_allocation_groups(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": True,
                        "variants": [
                            {"name": "Off", "status_override": "Enabled"},
                            {"name": "On", "status_override": "Disabled"},
                        ],
                        "allocation": {
                            "group": [
                                {"variant": "On", "groups": ["Group1"]},
                                {"variant": "Off", "groups": ["Group2"]},
                            ],
                        },
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "AlwaysOnFilter",
                                    "parameters": {},
                                }
                            ]
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOnFilter()])
        assert await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")) is None
        assert not await feature_manager.is_enabled("Alpha", TargetingContext(user_id="Adam", groups=["Group1"]))
        assert (
            await feature_manager.get_variant("Alpha", TargetingContext(user_id="Adam", groups=["Group1"]))
        ).name == "On"
        assert await feature_manager.is_enabled("Alpha", TargetingContext(user_id="Brittney", groups=["Group2"]))
        assert (
            await feature_manager.get_variant("Alpha", TargetingContext(user_id="Brittney", groups=["Group2"]))
        ).name == "Off"
        assert await feature_manager.is_enabled("Alpha", TargetingContext(user_id="Charlie", groups=["Group3"]))
        assert (
            await feature_manager.get_variant("Alpha", TargetingContext(user_id="Charlie", groups=["Group3"]))
        ) is None

    # method: is_enabled
    async def test_basic_feature_variant_allocation_percentile(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": True,
                        "variants": [
                            {"name": "Off", "status_override": "Enabled"},
                            {"name": "On", "status_override": "Disabled"},
                        ],
                        "allocation": {
                            "percentile": [
                                {"variant": "On", "from": 0, "to": 50},
                                {"variant": "Off", "from": 50, "to": 100},
                            ],
                        },
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "AlwaysOnFilter",
                                    "parameters": {},
                                }
                            ]
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOnFilter()])
        assert await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")).name == "Off"
        assert await feature_manager.is_enabled("Alpha", "Adam")
        assert (await feature_manager.get_variant("Alpha", "Adam")).name == "Off"
        assert not await feature_manager.is_enabled("Alpha", "Brittney")
        assert (await feature_manager.get_variant("Alpha", "Brittney")).name == "On"
        assert not await feature_manager.is_enabled("Alpha", TargetingContext(user_id="Brittney", groups=["Group1"]))
        assert (
            await feature_manager.get_variant("Alpha", TargetingContext(user_id="Brittney", groups=["Group1"]))
        ).name == "On"
        assert await feature_manager.is_enabled("Alpha", "Cassidy")
        assert (await feature_manager.get_variant("Alpha", "Cassidy")).name == "Off"

    # method: is_enabled
    async def test_basic_feature_variant_allocation_percentile_seeded(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {
                        "id": "Alpha",
                        "enabled": True,
                        "variants": [
                            {"name": "Off", "status_override": "Enabled"},
                            {"name": "On", "status_override": "Disabled"},
                        ],
                        "allocation": {
                            "percentile": [
                                {"variant": "On", "from": 0, "to": 50},
                                {"variant": "Off", "from": 50, "to": 100},
                            ],
                            "seed": "test-seed2",
                        },
                        "conditions": {
                            "client_filters": [
                                {
                                    "name": "AlwaysOnFilter",
                                    "parameters": {},
                                }
                            ]
                        },
                    }
                ]
            }
        }
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOnFilter()])
        assert await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")).name == "Off"
        assert not await feature_manager.is_enabled("Alpha", "Allison")
        assert (await feature_manager.get_variant("Alpha", "Allison")).name == "On"
        assert await feature_manager.is_enabled("Alpha", "Bubbles")
        assert (await feature_manager.get_variant("Alpha", "Bubbles")).name == "Off"
        assert await feature_manager.is_enabled("Alpha", TargetingContext(user_id="Bubbles", groups=["Group1"]))
        assert (
            await feature_manager.get_variant("Alpha", TargetingContext(user_id="Bubbles", groups=["Group1"]))
        ).name == "Off"
        assert await feature_manager.is_enabled("Alpha", "Cassidy")
        assert (await feature_manager.get_variant("Alpha", "Cassidy")).name == "Off"
        assert not await feature_manager.is_enabled("Alpha", "Dan")
        assert (await feature_manager.get_variant("Alpha", "Dan")).name == "On"


class AlwaysOnFilter(FeatureFilter):
    async def evaluate(self, context, **kwargs):
        return True
