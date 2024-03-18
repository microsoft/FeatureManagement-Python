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

        assert feature_manager.is_enabled("Alpha")
        assert not feature_manager.is_enabled("Beta")
        assert not feature_manager.is_enabled("Gamma")
        assert not feature_manager.is_enabled("Delta")
        assert feature_manager.is_enabled("Epsilon")
        assert feature_manager.is_enabled("Zeta")
        assert not feature_manager.is_enabled("Eta", user="Adam")
        assert feature_manager.is_enabled("Eta", user="Alice")
        assert feature_manager.is_enabled("Eta", user="Adam", groups=["Stage1"])
        assert feature_manager.is_enabled("Eta", groups=["Stage2"])
        assert feature_manager.is_enabled("Eta", user="Adam", groups=["Stage2"])
        assert feature_manager.is_enabled("Eta", user="Brittney", groups=["Stage2"])
        assert not feature_manager.is_enabled("Eta", groups=["Stage3"])
        assert not feature_manager.is_enabled("Eta", user="Alice", groups=["Stage3"])
        assert not feature_manager.is_enabled("Eta", user="Adam", groups=["Stage3"])
        assert not feature_manager.is_enabled("Eta", user="Dave", groups=["Stage1"])
        assert feature_manager.is_enabled("Theta", user="Adam")
        assert feature_manager.is_enabled("Theta", user="Adam", groups=["Stage1"])
        assert feature_manager.is_enabled("Theta", user="Adam", groups=["Stage2"])
        assert feature_manager.is_enabled("Theta", user="Adam", groups=["Stage3"])
        assert not feature_manager.is_enabled("Theta", user="Brittney")
        assert not feature_manager.is_enabled("Theta", user="Brittney", groups=["Stage1"])
        assert not feature_manager.is_enabled("Theta", user="Brittney", groups=["Stage2"])
        assert not feature_manager.is_enabled("Theta", user="Brittney", groups=["Stage2"])

    # method: is_enabled
    def test_requirement_type_any(self):
        f = open("tests/all_feature_flag_options.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        assert feature_manager.is_enabled("Iota")
        assert feature_manager.is_enabled("Kappa")
        assert feature_manager.is_enabled("Lambda")
        assert not feature_manager.is_enabled("Mu")

    # method: is_enabled
    def test_requirement_type_all(self):
        f = open("tests/all_feature_flag_options.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        assert not feature_manager.is_enabled("Nu", user="Adam")
        assert feature_manager.is_enabled("Xi", user="Adam")
