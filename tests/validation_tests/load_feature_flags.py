# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from featuremanagement import FeatureManager
import json


class LoadFeatureFlagsFromFile:
    @staticmethod
    def load_from_file(file):
        feature_flags_file = open("tests/validation_tests/" + file, "r")
        feature_flags = json.load(feature_flags_file)

        feature_manager = FeatureManager(feature_flags)
        assert feature_manager is not None

        return feature_manager
