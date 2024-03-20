# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement import FeatureManager
import json
import unittest


class TestFeatureFlagFile(unittest.TestCase):
    # method: is_enabled
    def test_single_filters(self):
        f = open("tests/all_feature_flag_options.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Enabled Feature Flag with no filters
        assert feature_manager.is_enabled("Alpha")

        # Disabed Feature Flag with no filters
        assert not feature_manager.is_enabled("Beta")

        # Feature Flag with Time Window filter, both start and end time have passed.
        assert not feature_manager.is_enabled("Gamma")

        # Feature Flag with Time Window filter, has a start and end time that haven't been reached.
        assert not feature_manager.is_enabled("Delta")

        # Feature Flag with Time Window filter, has a start time that has passed.
        assert feature_manager.is_enabled("Epsilon")

        # Feature Flag with Time Window filter, has an end time that has not passed.
        assert feature_manager.is_enabled("Zeta")

        # Feature Flag with Targeting filter, Adam is not part of the default rollout.
        assert not feature_manager.is_enabled("Eta", user="Adam")

        # Feature Flag with Targeting filter, Ellie is part of the default rollout.
        assert feature_manager.is_enabled("Eta", user="Ellie")

        # Feature Flag with Targeting filter, Alice is a targeted user.
        assert feature_manager.is_enabled("Eta", user="Alice")

        # Feature Flag with Targeting filter, Stage1 group is 100% targeted.
        assert feature_manager.is_enabled("Eta", user="Adam", groups=["Stage1"])

        # Feature Flag with Targeting filter, Stage2 group is 50% targeted.
        assert feature_manager.is_enabled("Eta", groups=["Stage2"])

        # Feature Flag with Targeting filter, Adam is enabled when part of Stage2 group.
        assert feature_manager.is_enabled("Eta", user="Adam", groups=["Stage2"])

        # Feature Flag with Targeting filter, Chad is not part of the Stage2 group rollout nor the default rollout.
        assert not feature_manager.is_enabled("Eta", user="Chad", groups=["Stage2"])

        # Feature Flag with Targeting filter, Stage 3 group is excluded.
        assert not feature_manager.is_enabled("Eta", groups=["Stage3"])

        # Feature Flag with Targeting filter, Alice is approved, but exlusion of group 3 overrides.
        assert not feature_manager.is_enabled("Eta", user="Alice", groups=["Stage3"])

        # Feature Flag with Targeting filter, Ellie is part of default rollout, but exlusion of group 3 overrides.
        assert not feature_manager.is_enabled("Eta", user="Ellie", groups=["Stage3"])

        # Feature Flag with Targeting filter, Stage 1 is 100% rolled out, but Dave is excluded.
        assert not feature_manager.is_enabled("Eta", user="Dave", groups=["Stage1"])

        # Feature Flag with Targeting filter, with just 50% rollout. Adama is not part of the 50%, Brittney is not, group isn't part of the rollout so value isn't changed.
        assert feature_manager.is_enabled("Theta", user="Adam")
        assert feature_manager.is_enabled("Theta", user="Adam", groups=["Stage1"])
        assert feature_manager.is_enabled("Theta", user="Adam", groups=["Stage2"])
        assert feature_manager.is_enabled("Theta", user="Adam", groups=["Stage3"])
        assert not feature_manager.is_enabled("Theta", user="Brittney")
        assert not feature_manager.is_enabled("Theta", user="Brittney", groups=["Stage1"])
        assert not feature_manager.is_enabled("Theta", user="Brittney", groups=["Stage2"])
        assert not feature_manager.is_enabled("Theta", user="Brittney", groups=["Stage3"])

    # method: is_enabled
    def test_requirement_type_any(self):
        f = open("tests/all_feature_flag_options.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Feature Flag with two feature filters, the first is true, second is false, so the flag is enabled.
        assert feature_manager.is_enabled("Iota")

        # Feature Flag with two feature filters, the first is false, second is true, so the flag is enabled.
        assert feature_manager.is_enabled("Kappa")

        # Feature Flag with two feature filters, same as Kappa, but specifies the requirement type.
        assert feature_manager.is_enabled("Lambda")

        # Feature Flag with two feature filters, same as Lambda, but both filters are false, so the flag is disabled.
        assert not feature_manager.is_enabled("Mu")

    # method: is_enabled
    def test_requirement_type_all(self):
        f = open("tests/all_feature_flag_options.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Feature Flag with two feature filters with the All requirement type, the first is true, second is false, so the flag is disabled.
        assert not feature_manager.is_enabled("Nu", user="Adam")

        # Feature Flag with two feature filters with the All requirement type, both are true, so the flag is enabled.
        assert feature_manager.is_enabled("Xi", user="Adam")
