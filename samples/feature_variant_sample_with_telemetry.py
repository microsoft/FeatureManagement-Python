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
from featuremanagement.azuremonitor import publish_telemetry, track_event


try:
    from azure.monitor.opentelemetry import configure_azure_monitor

    # Configure Azure Monitor
    configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
except ImportError:
    pass

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

with open(script_directory + "/formatted_feature_flags.json", "r", encoding="utf-8") as f:
    feature_flags = json.load(f)

# Initialize the feature manager with telemetry callback
feature_manager = FeatureManager(
    feature_flags, feature_filters=[RandomFilter()], on_feature_evaluated=publish_telemetry
)

# Evaluate the feature flag for the user
print(feature_manager.get_variant("TestVariants", "Adam").configuration)

# Track an event
track_event("TestEvent", "Adam")
