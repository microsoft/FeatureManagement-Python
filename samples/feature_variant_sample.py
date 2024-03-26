# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from featuremanagement import FeatureManager
from random_filter import RandomFilter
import json
import os
import sys
import time

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

f = open(script_directory + "/formatted_feature_flags.json", "r")

feature_flags = json.load(f)

feature_manager = FeatureManager(feature_flags, feature_filters=[RandomFilter()])

print(feature_manager.is_enabled("TestVariants", user="Adam"))
print(feature_manager.get_variant("TestVariants", user="Adam").configuration)

print(feature_manager.is_enabled("TestVariants", user="Cass"))
print(feature_manager.get_variant("TestVariants", user="Cass").configuration)

now = time.time()
t = 0
f = 0

for i in range(10000000):
    if feature_manager.get_variant("TestVariants", user=str(i)).name == "True_Override":
        t += 1
    else:
        f += 1

print(t, f)
print(time.time() - now)
