# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Tests for built-in feature filters."""

import inspect
import json
import pickle
import unittest
import pytest
from featuremanagement import FeatureManager, TargetingContext


class TestDefaultFeatureFlags(unittest.TestCase):
    def test_targeting_context_field_defaults_match_construction(self) -> None:
        defaults = TargetingContext._field_defaults
        parameters = inspect.signature(TargetingContext).parameters
        assert defaults == {name: parameter.default for name, parameter in parameters.items()}

        first = TargetingContext(**defaults)
        second = TargetingContext(**defaults)
        assert first == TargetingContext()
        first.groups.append("Admins")
        assert second.groups == []
        assert TargetingContext().groups == []

    def test_targeting_context_fields_are_read_only(self) -> None:
        context = TargetingContext("Alice", ["Admins"])
        for field, value in (("user_id", "Bob"), ("groups", ["Users"]), ("extra", True)):
            with self.subTest(field=field), pytest.raises(AttributeError):
                setattr(context, field, value)
        assert context == TargetingContext("Alice", ["Admins"])

    def test_targeting_context_serialization(self) -> None:
        context = TargetingContext("Alice", ["Admins"])
        assert json.dumps(context) == '["Alice", ["Admins"]]'
        for protocol in (0, pickle.HIGHEST_PROTOCOL):
            with self.subTest(protocol=protocol):
                restored = pickle.loads(pickle.dumps(context, protocol=protocol))
                assert type(restored) is TargetingContext
                assert restored == context
                restored.groups.append("Users")
                assert context.groups == ["Admins"]

    def test_targeting_context_helpers_preserve_subclass(self) -> None:
        groups = ["Admins"]
        context = TargetingContext._make(("Alice", groups))
        assert type(context) is TargetingContext
        assert context == TargetingContext("Alice", groups)
        assert context.groups is groups

        renamed = context._replace(user_id="Bob")
        assert type(renamed) is TargetingContext
        assert renamed == TargetingContext("Bob", ["Admins"])
        assert renamed.groups is groups
        assert context == TargetingContext("Alice", ["Admins"])

    def test_targeting_context_default_groups_are_independent(self) -> None:
        first = TargetingContext(user_id="Alice")
        second = TargetingContext(user_id="Bob")
        explicit_none = TargetingContext(groups=None)

        first.groups.append("Admins")

        assert first.groups == ["Admins"]
        assert second.groups == []
        assert explicit_none.groups == []
        assert TargetingContext().groups == []

    def test_targeting_context_preserves_supplied_groups(self) -> None:
        groups: list[str] = []
        context = TargetingContext("Alice", groups)

        context.groups.append("Admins")

        assert context.user_id == "Alice"
        assert context.groups is groups
        assert groups == ["Admins"]

    def test_invalid_feature_flags(self):
        with self.assertRaises(AttributeError):
            FeatureManager("")

    # method: feature_manager_creation
    def test_feature_manager_creation_with_targeting(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
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
        assert feature_manager.is_enabled("Target", "Adam")
        # Brian is not part of the 50% or default 50% of users
        assert not feature_manager.is_enabled("Target", "Belle")
        # Brian is enabled because all of Stage 1 is enabled
        assert feature_manager.is_enabled("Target", TargetingContext(user_id="Belle", groups=["Stage1"]))
        # Brian is not enabled because he is not in Stage 2, group isn't looked at when user is targeted
        assert not feature_manager.is_enabled("Target", TargetingContext(user_id="Belle", groups=["Stage2"]))

        first = TargetingContext("Belle")
        first.groups.append("Stage1")
        assert feature_manager.is_enabled("Target", first)
        assert not feature_manager.is_enabled("Target", TargetingContext("Belle"))

    # method: feature_manager_creation
    def test_feature_manager_creation_with_time_window(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
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
        assert feature_manager.is_enabled("Alpha")
        assert feature_manager.is_enabled("Beta")
        assert not feature_manager.is_enabled("Gamma")
        assert not feature_manager.is_enabled("Delta")
        assert feature_manager.is_enabled("Epsilon")
        assert not feature_manager.is_enabled("Foxtrot")

    def test_feature_manager_invalid_feature_flag(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
                    {},
                ]
            }
        }

        feature_manager = FeatureManager(feature_flags)
        assert not feature_manager.is_enabled("Alpha")

        feature_flags["feature_management"]["feature_flags"][0]["id"] = 1

        with pytest.raises(ValueError, match="Invalid setting 'id' with value '1' for feature '1'."):
            feature_manager = FeatureManager(feature_flags)
            feature_manager.is_enabled(1)

        feature_flags["feature_management"]["feature_flags"][0]["id"] = "featureFlagId"
        feature_flags["feature_management"]["feature_flags"][0]["enabled"] = "true"

        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        feature_flags["feature_management"]["feature_flags"][0]["conditions"] = {}
        feature_flags["feature_management"]["feature_flags"][0]["conditions"]["client_filters"] = []

        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        feature_flags["feature_management"]["feature_flags"][0]["conditions"]["client_filters"].append({})

        with pytest.raises(ValueError, match="Feature flag featureFlagId is missing filter name."):
            FeatureManager(feature_flags)
            feature_manager.is_enabled("featureFlagId")

    def test_feature_manager_requirement_type(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
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
                            ],
                            "requirement_type": "All",
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
                                        "Start": "Wed, 01 Jan 2020 00:00:00 GMT",
                                    },
                                },
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "End": "Wed, 01 Jan 2020 00:00:00 GMT",
                                    },
                                },
                            ],
                            "requirement_type": "All",
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
                                        "Start": "Wed, 01 Jan 2020 00:00:00 GMT",
                                    },
                                },
                                {
                                    "name": "Microsoft.TimeWindow",
                                    "parameters": {
                                        "End": "Wed, 01 Jan 2020 00:00:00 GMT",
                                    },
                                },
                            ],
                            "requirement_type": "Any",
                        },
                    },
                ]
            }
        }

        feature_manager = FeatureManager(feature_flags)

        assert feature_manager.is_enabled("Alpha")
        # The second TimeWindow filter failed
        assert not feature_manager.is_enabled("Beta")
        assert feature_manager.is_enabled("Gamma")

    def test_feature_manager_with_targeting_accessor(self):
        feature_flags = {
            "feature_management": {
                "feature_flags": [
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

        user_id = "Adam"
        group_id = None

        def my_targeting_accessor() -> TargetingContext:
            if group_id:
                return TargetingContext(user_id=user_id, groups=[group_id])
            return TargetingContext(user_id=user_id)

        feature_manager = FeatureManager(feature_flags, targeting_context_accessor=my_targeting_accessor)
        assert feature_manager is not None
        # Adam is in the user audience
        assert feature_manager.is_enabled("Target")
        # Belle is not part of the 50% or default 50% of users
        user_id = "Belle"
        assert not feature_manager.is_enabled("Target")
        # Belle is enabled because all of Stage 1 is enabled
        group_id = "Stage1"
        assert feature_manager.is_enabled("Target")
        # Belle is not enabled because he is not in Stage 2, group isn't looked at when user is targeted
        group_id = "Stage2"
        assert not feature_manager.is_enabled("Target")
