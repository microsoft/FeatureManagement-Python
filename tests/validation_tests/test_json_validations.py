# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import unittest
import json
from featuremanagement import FeatureManager

FILE_PATH = "tests/validation_tests/"
SAMPLE_JSON_KEY = ".sample.json"
TESTS_JSON_KEY = ".tests.json"
TEST_ID_KEY = "TestID"
EXPECTED_RESULT_KEY = "ExpectedResult"
FEATURE_FLAG_NAME_KEY = "FeatureFlagName"
INPUTS_KEY = "Inputs"
DESCRIPTION_KEY = "Description"


class TestNoFiltersFromFile(unittest.TestCase):
    # method: is_enabled
    def test_no_filters(self):
        test_key = "NoFilters"
        self.run_tests(test_key)

    # method: is_enabled
    def test_time_window_filter(self):
        test_key = "TimeWindowFilter"
        self.run_tests(test_key)

    # method: is_enabled
    def test_targeting_filter(self):
        test_key = "TargetingFilter"
        self.run_tests(test_key)

    # method: is_enabled
    def test_targeting_filter_modified(self):
        test_key = "TargetingFilter.modified"
        self.run_tests(test_key)

    # method: is_enabled
    def test_requirement_type(self):
        test_key = "RequirementType"
        self.run_tests(test_key)

    @staticmethod
    def load_from_file(file):
        with open("tests/validation_tests/" + file, "r", encoding="utf-8") as feature_flags_file:
            feature_flags = json.load(feature_flags_file)

        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        return feature_manager


    # method: is_enabled
    def run_tests(self, test_key):
        feature_manager = self.load_from_file(test_key + SAMPLE_JSON_KEY)

        with open(FILE_PATH + test_key + TESTS_JSON_KEY, "r", encoding="utf-8") as feature_flag_test_file:
            feature_flag_tests = json.load(feature_flag_test_file)

        for feature_flag_test in feature_flag_tests:
            expected_result = feature_flag_test[EXPECTED_RESULT_KEY]
            failed_description = (
                "Test " + feature_flag_test[TEST_ID_KEY] + " failed. Description: " + feature_flag_test[DESCRIPTION_KEY]
            )

            if isinstance(expected_result, bool):
                if INPUTS_KEY in feature_flag_test:
                    user = feature_flag_test[INPUTS_KEY].get("user", None)
                    groups = feature_flag_test[INPUTS_KEY].get("groups", [])
                    assert (
                        feature_manager.is_enabled(feature_flag_test[FEATURE_FLAG_NAME_KEY], user=user, groups=groups)
                        == expected_result
                    ), failed_description
                else:
                    assert (
                        feature_manager.is_enabled(feature_flag_test[FEATURE_FLAG_NAME_KEY]) == expected_result
                    ), failed_description
            else:
                with self.assertRaises(ValueError):
                    feature_manager.is_enabled(feature_flag_test[FEATURE_FLAG_NAME_KEY])
