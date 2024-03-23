# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from tests.validation_tests.load_feature_flags import LoadFeatureFlagsFromFile
import unittest


class TestNoFiltersFromFile(LoadFeatureFlagsFromFile, unittest.TestCase):
    # method: is_enabled
    def test_enabled(self):
        feature_manager = self.load_from_file("NoFilters.sample.json")

        # Enabled Feature Flag with no filters
        assert feature_manager.is_enabled("BooleanTrueFeatureFlag")

        # Enabled Feature Flag with no filters
        assert feature_manager.is_enabled("StringTrueFeatureFlag")

        # A Feature Flag with just an id and enabled field set to true
        assert feature_manager.is_enabled("MinimalFeatureFlag")

        # A Feature Flag with no conditions
        assert feature_manager.is_enabled("NoConditions")

    def test_disabled(self):
        feature_manager = self.load_from_file("NoFilters.sample.json")

        # Disabed Feature Flag with no filters
        assert not feature_manager.is_enabled("BooleanFalseFeatureFlag")

        # Disabed Feature Flag with no filters
        assert not feature_manager.is_enabled("StringFalseFeatureFlag")

        # A Feature Flag with just an id
        assert not feature_manager.is_enabled("NoEnabled")

    def test_invalid(self):
        feature_manager = self.load_from_file("NoFilters.sample.json")

        # enabled is non-boolean
        with self.assertRaises(ValueError) as ex:
            feature_manager.is_enabled("InvalidEnabledFeatureFlag")
            assert "Invalid value for 'enabled' in feature flag 'InvalidEnabledFeatureFlag'." in str(ex)
