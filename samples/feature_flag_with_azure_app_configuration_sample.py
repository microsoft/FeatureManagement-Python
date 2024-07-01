# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from time import sleep
import os
from azure.appconfiguration.provider import load
from random_filter import RandomFilter
from featuremanagement import FeatureManager, TargetingContext

connection_string = os.environ["APPCONFIGURATION_CONNECTION_STRING"]

# Connecting to Azure App Configuration using AAD
config = load(connection_string=connection_string, feature_flag_enabled=True, feature_flag_refresh_enabled=True)

feature_manager = FeatureManager(config, feature_filters=[RandomFilter()])


def check_for_changes():
    alpha = feature_manager.is_enabled("Alpha")
    # Is always true
    print("Alpha is ", alpha is True)
    while feature_manager.is_enabled("Alpha") == alpha:
        sleep(5)
        config.refresh()

    alpha = feature_manager.is_enabled("Alpha")
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
check_for_changes()
