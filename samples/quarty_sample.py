# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------

import uuid
import os
from quart import Quart, request, session
from quart.sessions import SecureCookieSessionInterface
from azure.appconfiguration.provider import load
from azure.identity import DefaultAzureCredential
from featuremanagement.aio import FeatureManager
from featuremanagement import TargetingContext

try:
    from azure.monitor.opentelemetry import configure_azure_monitor  # pylint: disable=ungrouped-imports

    # Configure Azure Monitor
    configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
except ImportError:
    pass

app = Quart(__name__)
app.session_interface = SecureCookieSessionInterface()
app.secret_key = os.urandom(24)

endpoint = os.environ.get("APPCONFIGURATION_ENDPOINT_STRING")
credential = DefaultAzureCredential()


async def my_targeting_accessor() -> TargetingContext:
    session_id = ""
    if "Session-ID" in request.headers:
        session_id = request.headers["Session-ID"]
    return TargetingContext(user_id=session_id)


# Connecting to Azure App Configuration using AAD
config = load(endpoint=endpoint, credential=credential, feature_flag_enabled=True, feature_flag_refresh_enabled=True)

# Load feature flags and set up targeting context accessor
feature_manager = FeatureManager(config, targeting_context_accessor=my_targeting_accessor)


@app.before_request
async def before_request():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())  # Generate a new session ID
    request.headers["Session-ID"] = session["session_id"]


@app.route("/")
async def hello():
    variant = await feature_manager.get_variant("Message")
    return str(variant.configuration if variant else "No variant found")


app.run()
