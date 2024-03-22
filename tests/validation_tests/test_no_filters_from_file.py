# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from tests.validation_tests.load_feature_flags import LoadFeatureFlagsFromFile
import unittest


class TestNoFiltersFromFile(LoadFeatureFlagsFromFile, unittest.TestCase):
    # method: is_enabled
    def test_enabled_filter(self):
        feature_manager = self.load_from_file("NoFilters.sample.json")

        # Enabled Feature Flag with no filters
        assert feature_manager.is_enabled("EnabledFeatureFlag")

    def test_disabled_filter(self):
        feature_manager = self.load_from_file("NoFilters.sample.json")

        # Disabed Feature Flag with no filters
        assert not feature_manager.is_enabled("DisabledFeatureFlag")
