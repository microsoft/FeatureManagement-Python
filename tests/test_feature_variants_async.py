# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement.aio import FeatureManager, FeatureFilter
from unittest import IsolatedAsyncioTestCase


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
        assert (await feature_manager.get_variant("Alpha")).name is "On"

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
        assert await feature_manager.is_enabled("Alpha")
        assert (await feature_manager.get_variant("Alpha")).name is "Off"

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
        assert (await feature_manager.get_variant("Alpha")).name is "Off"

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
        assert not await feature_manager.is_enabled("Alpha", user="Adam")
        assert (await feature_manager.get_variant("Alpha", user="Adam")).name is "On"
        assert await feature_manager.is_enabled("Alpha", user="Brittney")
        assert (await feature_manager.get_variant("Alpha", user="Brittney")).name is "Off"
        assert await feature_manager.is_enabled("Alpha", user="Charlie")
        assert (await feature_manager.get_variant("Alpha", user="Charlie")) is None

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
        assert not await feature_manager.is_enabled("Alpha", user="Adam", groups=["Group1"])
        assert (await feature_manager.get_variant("Alpha", user="Adam", groups=["Group1"])).name is "On"
        assert await feature_manager.is_enabled("Alpha", user="Brittney", groups=["Group2"])
        assert (await feature_manager.get_variant("Alpha", user="Brittney", groups=["Group2"])).name is "Off"
        assert await feature_manager.is_enabled("Alpha", user="Charlie", groups=["Group3"])
        assert (await feature_manager.get_variant("Alpha", user="Charlie", groups=["Group3"])) is None

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
        assert (await feature_manager.get_variant("Alpha")).name is "Off"
        assert await feature_manager.is_enabled("Alpha", user="Adam")
        assert (await feature_manager.get_variant("Alpha", user="Adam")).name is "Off"
        assert not await feature_manager.is_enabled("Alpha", user="Brittney")
        assert (await feature_manager.get_variant("Alpha", user="Brittney")).name is "On"
        assert not await feature_manager.is_enabled("Alpha", user="Brittney", groups=["Group1"])
        assert (await feature_manager.get_variant("Alpha", user="Brittney", groups=["Group1"])).name is "On"
        assert await feature_manager.is_enabled("Alpha", user="Cassidy")
        assert (await feature_manager.get_variant("Alpha", user="Cassidy")).name is "Off"

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
        assert (await feature_manager.get_variant("Alpha")).name is "Off"
        assert not await feature_manager.is_enabled("Alpha", user="Allison")
        assert (await feature_manager.get_variant("Alpha", user="Allison")).name is "On"
        assert await feature_manager.is_enabled("Alpha", user="Bubbles")
        assert (await feature_manager.get_variant("Alpha", user="Bubbles")).name is "Off"
        assert await feature_manager.is_enabled("Alpha", user="Bubbles", groups=["Group1"])
        assert (await feature_manager.get_variant("Alpha", user="Bubbles", groups=["Group1"])).name is "Off"
        assert await feature_manager.is_enabled("Alpha", user="Cassidy")
        assert (await feature_manager.get_variant("Alpha", user="Cassidy")).name is "Off"
        assert not await feature_manager.is_enabled("Alpha", user="Dan")
        assert (await feature_manager.get_variant("Alpha", user="Dan")).name is "On"


class AlwaysOnFilter(FeatureFilter):
    async def evaluate(self, context, **kwargs):
        return True
