# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import unittest
from featuremanagement import FeatureManager, FeatureFilter, TargetingContext


class TestFeatureVariants(unittest.TestCase):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName=methodName)
        self.called_telemetry = False

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
        assert feature_manager.get_variant("Alpha").name == "On"

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

        # Enabled = False takes precedence over status_override
        assert not feature_manager.is_enabled("Alpha")
        assert feature_manager.get_variant("Alpha").name == "Off"

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
        assert feature_manager.get_variant("Alpha").name == "Off"

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
        assert feature_manager.get_variant("Alpha") is None
        assert not feature_manager.is_enabled("Alpha", "Adam")
        assert feature_manager.get_variant("Alpha", "Adam").name == "On"
        assert feature_manager.is_enabled("Alpha", "Brittney")
        assert feature_manager.get_variant("Alpha", "Brittney").name == "Off"
        assert feature_manager.is_enabled("Alpha", "Charlie")
        assert feature_manager.get_variant("Alpha", "Charlie") is None

    def test_user_and_group_allocation(self):
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
        assert feature_manager.is_enabled("Alpha")
        assert feature_manager.get_variant("Alpha") is None
        assert not feature_manager.is_enabled("Alpha", TargetingContext(user_id="NotAdam", groups=["Group1"]))
        assert feature_manager.get_variant("Alpha", TargetingContext(user_id="NotAdam", groups=["Group1"])).name == "On"
        assert not feature_manager.is_enabled("Alpha", TargetingContext(user_id="NotAdam", groups=["Group1"]))
        assert feature_manager.get_variant("Alpha", TargetingContext(groups=["Group2"])).name == "Off"
        assert feature_manager.is_enabled("Alpha", TargetingContext(user_id="NotCharlie", groups=["Group3"]))
        assert feature_manager.get_variant("Alpha", TargetingContext(user_id="NotCharlie", groups=["Group3"])) is None

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
        feature_manager = FeatureManager(feature_flags, feature_filters=[AlwaysOnFilter()])
        assert feature_manager.is_enabled("Alpha")
        assert feature_manager.get_variant("Alpha") is None
        assert not feature_manager.is_enabled("Alpha", TargetingContext(user_id="Adam", groups=["Group1"]))
        assert feature_manager.get_variant("Alpha", TargetingContext(user_id="Adam", groups=["Group1"])).name == "On"
        assert feature_manager.is_enabled("Alpha", TargetingContext(user_id="Brittney", groups=["Group2"]))
        assert (
            feature_manager.get_variant("Alpha", TargetingContext(user_id="Brittney", groups=["Group2"])).name == "Off"
        )
        assert feature_manager.is_enabled("Alpha", TargetingContext(user_id="Charlie", groups=["Group3"]))
        assert feature_manager.get_variant("Alpha", TargetingContext(user_id="Charlie", groups=["Group3"])) is None

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
        assert feature_manager.get_variant("Alpha").name == "Off"
        assert feature_manager.is_enabled("Alpha", "Adam")
        assert feature_manager.get_variant("Alpha", "Adam").name == "Off"
        assert not feature_manager.is_enabled("Alpha", "Brittney")
        assert feature_manager.get_variant("Alpha", "Brittney").name == "On"
        assert not feature_manager.is_enabled("Alpha", TargetingContext(user_id="Brittney", groups=["Group1"]))
        assert (
            feature_manager.get_variant("Alpha", TargetingContext(user_id="Brittney", groups=["Group1"])).name == "On"
        )
        assert feature_manager.is_enabled("Alpha", "Cassidy")
        assert feature_manager.get_variant("Alpha", "Cassidy").name == "Off"

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
        assert feature_manager.get_variant("Alpha").name == "Off"
        assert not feature_manager.is_enabled("Alpha", "Allison")
        assert feature_manager.get_variant("Alpha", "Allison").name == "On"
        assert feature_manager.is_enabled("Alpha", "Bubbles")
        assert feature_manager.get_variant("Alpha", "Bubbles").name == "Off"
        assert feature_manager.is_enabled("Alpha", TargetingContext(user_id="Bubbles", groups=["Group1"]))
        assert (
            feature_manager.get_variant("Alpha", TargetingContext(user_id="Bubbles", groups=["Group1"])).name == "Off"
        )
        assert feature_manager.is_enabled("Alpha", "Cassidy")
        assert feature_manager.get_variant("Alpha", "Cassidy").name == "Off"
        assert not feature_manager.is_enabled("Alpha", "Dan")
        assert feature_manager.get_variant("Alpha", "Dan").name == "On"

    # method: feature_manager_creation
    def test_feature_with_telemetry(self):
        self.called_telemetry = False
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
                        "telemetry": {"enabled": "true"},
                    }
                ]
            }
        }

        feature_manager = FeatureManager(feature_flags, on_feature_evaluated=self.fake_telemetry_callback)
        assert feature_manager is not None
        assert not feature_manager.is_enabled("Alpha")
        assert feature_manager.get_variant("Alpha").name == "On"
        assert self.called_telemetry

    def fake_telemetry_callback(self, evaluation_event):
        assert evaluation_event
        self.called_telemetry = True


class AlwaysOnFilter(FeatureFilter):
    def evaluate(self, context, **kwargs):
        return True
