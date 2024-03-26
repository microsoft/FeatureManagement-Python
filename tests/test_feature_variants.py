# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement import FeatureManager, FeatureFilter


class TestFeatureVariants:
    # method: is_enabled
    def test_basic_feature_variant_override_enabled(self):
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
        assert not feature_manager.is_enabled("Alpha")

    # method: is_enabled
    def test_basic_feature_variant_override_disabled(self):
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
        assert feature_manager.is_enabled("Alpha")

    # method: is_enabled
    def test_basic_feature_variant_no_override(self):
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
        assert not feature_manager.is_enabled("Alpha")

    # method: is_enabled
    def test_basic_feature_variant_allocation_users(self):
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
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Alpha", user="Adam")
        assert feature_manager.is_enabled("Alpha", user="Brittney")
        assert feature_manager.is_enabled("Alpha", user="Charlie")

    # method: is_enabled
    def test_basic_feature_variant_allocation_groups(self):
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
        test = AlwaysOnFilter()
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOnFilter()])
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Alpha", user="Adam", groups=["Group1"])
        assert feature_manager.is_enabled("Alpha", user="Brittney", groups=["Group2"])
        assert feature_manager.is_enabled("Alpha", user="Charlie", groups=["Group3"])

    # method: is_enabled
    def test_basic_feature_variant_allocation_percentile(self):
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
        assert feature_manager.is_enabled("Alpha")
        assert feature_manager.is_enabled("Alpha", user="Adam")
        assert not feature_manager.is_enabled("Alpha", user="Babs")
        assert not feature_manager.is_enabled("Alpha", user="Babs", groups=["Group1"])
        assert feature_manager.is_enabled("Alpha", user="Charlie")

    # method: is_enabled
    def test_basic_feature_variant_allocation_percentile_seeded(self):
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
        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Alpha", user="Alison")
        assert feature_manager.is_enabled("Alpha", user="Brittney")
        assert feature_manager.is_enabled("Alpha", user="Brittney", groups=["Group1"])
        assert feature_manager.is_enabled("Alpha", user="Cassidy")
        assert not feature_manager.is_enabled("Alpha", user="Dan")


class AlwaysOnFilter(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return True