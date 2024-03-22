# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement import FeatureManager
import json
import unittest


class TestNoFiltersFromFile(unittest.TestCase):
    # method: is_enabled
    def test_single_filters(self):
        f = open("tests/validation_tests/NoFilters.sample.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Enabled Feature Flag with no filters
        assert feature_manager.is_enabled("EnabledFeatureFlag")

        # Disabed Feature Flag with no filters
        assert not feature_manager.is_enabled("DisabledFeatureFlag")
