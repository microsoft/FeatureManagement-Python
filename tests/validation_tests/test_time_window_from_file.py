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
        f = open("tests/validation_tests/TimeWindowFilter.sample.json", "r")

        feature_flags = json.load(f)
        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        # Feature Flag with Time Window filter, both start and end time have passed.
        assert not feature_manager.is_enabled("PastTimeWindow")

        # Feature Flag with Time Window filter, has a start and end time that haven't been reached.
        assert not feature_manager.is_enabled("FutureTimeWindow")

        # Feature Flag with Time Window filter, has a start and end time that haven't been reached.
        assert feature_manager.is_enabled("PresentTimeWindow")

        # Feature Flag with Time Window filter, has a start time that has passed.
        assert feature_manager.is_enabled("StartedTimeWindow")

        # Feature Flag with Time Window filter, has an end time that has not passed.
        assert feature_manager.is_enabled("WillEndTimeWindow")
