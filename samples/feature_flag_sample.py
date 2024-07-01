# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

import json
import os
import sys
from random_filter import RandomFilter
from featuremanagement import FeatureManager, TargetingContext

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

with open(script_directory + "/formatted_feature_flags.json", "r", encoding="utf-8") as f:
    feature_flags = json.load(f)

feature_manager = FeatureManager(feature_flags, feature_filters=[RandomFilter()])

# Is always true
print("Alpha is ", feature_manager.is_enabled("Alpha"))
# Is always false
print("Beta is ", feature_manager.is_enabled("Beta"))
# Is false 50% of the time
print("Gamma is ", feature_manager.is_enabled("Gamma"))
# Is true between two dates
print("Delta is ", feature_manager.is_enabled("Delta"))
# Is true After 06-27-2023
print("Sigma is ", feature_manager.is_enabled("Sigma"))
# Is true Before 06-28-2023
print("Epsilon is ", feature_manager.is_enabled("Epsilon"))
# Target is true for Adam, group Stage 1, and 50% of users
print("Target is ", feature_manager.is_enabled("Target", TargetingContext(user_id="Adam")))
print("Target is ", feature_manager.is_enabled("Target", TargetingContext(user_id="Brian")))
