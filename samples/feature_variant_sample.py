# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import json
import os
import sys
from random_filter import RandomFilter
from featuremanagement import FeatureManager


script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

with open(script_directory + "/formatted_feature_flags.json", "r", encoding="utf-8") as f:
    feature_flags = json.load(f)

feature_manager = FeatureManager(feature_flags, feature_filters=[RandomFilter()])

print(feature_manager.is_enabled("TestVariants", "Adam"))
print(feature_manager.get_variant("TestVariants", "Adam").configuration)

print(feature_manager.is_enabled("TestVariants", "Cass"))
print(feature_manager.get_variant("TestVariants", "Cass").configuration)
