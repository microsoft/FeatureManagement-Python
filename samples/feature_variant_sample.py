from featuremanagement import FeatureManager
import os

from azure.appconfiguration.provider import load

connection_string = os.environ["APPCONFIGURATION_CONNECTION_STRING"]

# Connecting to Azure App Configuration using AAD
config = load(
    connection_string=connection_string, feature_flag_enabled=True, feature_flag_refresh_enabled=True
)

feature_manager = FeatureManager(config)

print(feature_manager.is_enabled("varient_true"))