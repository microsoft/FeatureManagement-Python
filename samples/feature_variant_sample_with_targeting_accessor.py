# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import json
import os
import sys
from random_filter import RandomFilter
from featuremanagement import FeatureManager, TargetingContext


script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

with open(script_directory + "/formatted_feature_flags.json", "r", encoding="utf-8") as f:
    feature_flags = json.load(f)

user_id = "Adam"


def my_targeting_accessor() -> TargetingContext:
    return TargetingContext(user_id=user_id)


feature_manager = FeatureManager(
    feature_flags, feature_filters=[RandomFilter()], targeting_context_accessor=my_targeting_accessor
)

print(feature_manager.is_enabled("TestVariants"))
print(feature_manager.get_variant("TestVariants").configuration)

user_id = "Ellie"

print(feature_manager.is_enabled("TestVariants"))
print(feature_manager.get_variant("TestVariants").configuration)
