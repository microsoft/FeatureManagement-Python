# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import sys
import logging
from importlib import reload
from unittest.mock import patch
import pytest
from featuremanagement import EvaluationEvent, send_telemetry_appinsights, FeatureFlag, Variant, VaraintAssignmentReason


@pytest.mark.usefixtures("caplog")
class TestSendTelemetryAppinsights:

    def test_send_telemetry_appinsights(self):
        evaluation_event = EvaluationEvent()
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"
        evaluation_event.variant = variant
        evaluation_event.reason = VaraintAssignmentReason.NONE

        with patch("featuremanagement._send_telemetry_appinsights.track_event") as mock_track_event:
            send_telemetry_appinsights(evaluation_event)
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert mock_track_event.call_args[0][1]["Variant"] == "TestVariant"
            assert mock_track_event.call_args[0][1]["Reason"] == "NONE"

    def test_send_telemetry_appinsights_no_user(self):
        evaluation_event = EvaluationEvent()
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = False
        evaluation_event.variant = variant
        evaluation_event.reason = VaraintAssignmentReason.NONE

        with patch("featuremanagement._send_telemetry_appinsights.track_event") as mock_track_event:
            send_telemetry_appinsights(evaluation_event)
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "False"
            assert "TargetingId" not in mock_track_event.call_args[0][1]
            assert mock_track_event.call_args[0][1]["Variant"] == "TestVariant"
            assert mock_track_event.call_args[0][1]["Reason"] == "NONE"

    def test_send_telemetry_appinsights_no_variant(self):
        evaluation_event = EvaluationEvent()
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"

        with patch("featuremanagement._send_telemetry_appinsights.track_event") as mock_track_event:
            send_telemetry_appinsights(evaluation_event)
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert "Variant" not in mock_track_event.call_args[0][1]
            assert "Reason" not in mock_track_event.call_args[0][1]

    def test_send_telemetry_appinsights_no_import(self, caplog):
        evaluation_event = EvaluationEvent()
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True

        with patch.dict("sys.modules", {"azure.monitor.events.extension": None}):
            reload(sys.modules["featuremanagement._send_telemetry_appinsights"])
            caplog.set_level(logging.WARNING)
            send_telemetry_appinsights(evaluation_event)
            assert "Telemetry will not be sent to Application Insights." in caplog.text
