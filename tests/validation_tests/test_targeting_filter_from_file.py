# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement import FeatureManager
import json
import unittest


class TestTargetingFilterFromFile(unittest.TestCase):
    # method: is_enabled
    def test_complex_filter(self):
        f = open("tests/validation_tests/TargetingFilter.sample.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Feature Flag with Targeting filter, Adam is not part of the default rollout.
        assert not feature_manager.is_enabled("ComplexTargeting", user="Aiden")

        # Feature Flag with Targeting filter, Blossom is part of the default rollout.
        assert feature_manager.is_enabled("ComplexTargeting", user="Blossom")

        # Feature Flag with Targeting filter, Alice is a targeted user.
        assert feature_manager.is_enabled("ComplexTargeting", user="Alice")

        # Feature Flag with Targeting filter, Stage1 group is 100% targeted.
        assert feature_manager.is_enabled("ComplexTargeting", user="Aiden", groups=["Stage1"])

        # Feature Flag with Targeting filter, Stage2 group is 50% targeted.
        assert not feature_manager.is_enabled("ComplexTargeting", groups=["Stage2"])

        # Feature Flag with Targeting filter, Aiden is enabled when part of Stage2 group.
        assert feature_manager.is_enabled("ComplexTargeting", user="Aiden", groups=["Stage2"])

        # Feature Flag with Targeting filter, Chad is not part of the Stage2 group rollout nor the default rollout.
        assert not feature_manager.is_enabled("ComplexTargeting", user="Chad", groups=["Stage2"])

        # Feature Flag with Targeting filter, Stage 3 group is excluded.
        assert not feature_manager.is_enabled("ComplexTargeting", groups=["Stage3"])

        # Feature Flag with Targeting filter, Alice is approved, but exlusion of group 3 overrides.
        assert not feature_manager.is_enabled("ComplexTargeting", user="Alice", groups=["Stage3"])

        # Feature Flag with Targeting filter, Blossom is part of default rollout, but exlusion of group 3 overrides.
        assert not feature_manager.is_enabled("ComplexTargeting", user="Blossom", groups=["Stage3"])

        # Feature Flag with Targeting filter, Stage 1 is 100% rolled out, but Dave is excluded.
        assert not feature_manager.is_enabled("ComplexTargeting", user="Dave", groups=["Stage1"])

    def test_rollout_percentage(self):
        f = open("tests/validation_tests/TargetingFilter.sample.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Feature Flag with Targeting filter, with just 50% rollout. Aiden is not part of the 50%, Brittney is not, group isn't part of the rollout so value isn't changed.
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden")
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden", groups=["Stage1"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden", groups=["Stage2"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden", groups=["Stage3"])
        assert not feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney")
        assert not feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney", groups=["Stage1"])
        assert not feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney", groups=["Stage2"])
        assert not feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney", groups=["Stage3"])

    def test_rollout_percentage_modified(self):
        f = open("tests/validation_tests/TargetingFilter.modified.sample.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Feature Flag with Targeting filter, with just 50% rollout. Aiden is not part of the 50%, Brittney is not, group isn't part of the rollout so value isn't changed.
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden")
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden", groups=["Stage1"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden", groups=["Stage2"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Aiden", groups=["Stage3"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney")
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney", groups=["Stage1"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney", groups=["Stage2"])
        assert feature_manager.is_enabled("RolloutPercentageUpdate", user="Brittney", groups=["Stage3"])