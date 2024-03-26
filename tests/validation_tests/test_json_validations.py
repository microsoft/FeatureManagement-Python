# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from tests.validation_tests.load_feature_flags import LoadFeatureFlagsFromFile
import unittest
import json

file_path = "tests/validation_tests/"
sample_json_key = ".sample.json"
tests_json_key = ".tests.json"
expected_result_key = "Expected Result"
feature_flag_name_key = "Feature Flag Name"


class TestNoFiltersFromFile(LoadFeatureFlagsFromFile, unittest.TestCase):
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

    # method: is_enabled
    def run_tests(self, test_key):
        feature_manager = self.load_from_file(test_key + sample_json_key)

        feature_flag_test_file = open(file_path + test_key + tests_json_key, "r")
        feature_flag_tests = json.load(feature_flag_test_file)

        for feature_flag_test in feature_flag_tests:
            expected_result = feature_flag_test[expected_result_key]
            failed_description = (
                "Test " + feature_flag_test["Test ID"] + " failed. Description: " + feature_flag_test["Description"]
            )

            if isinstance(expected_result, bool):
                if "Inputs" in feature_flag_test:
                    user = feature_flag_test["Inputs"].get("user", None)
                    groups = feature_flag_test["Inputs"].get("groups", [])
                    assert (
                        feature_manager.is_enabled(feature_flag_test[feature_flag_name_key], user=user, groups=groups)
                        == expected_result
                    ), failed_description
                else:
                    assert (
                        feature_manager.is_enabled(feature_flag_test[feature_flag_name_key]) == expected_result
                    ), failed_description
            else:
                with self.assertRaises(ValueError):
                    feature_manager.is_enabled(feature_flag_test[feature_flag_name_key]), failed_description
