# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import sys
import logging
from unittest import mock
from importlib import reload
from unittest.mock import patch
import pytest
from featuremanagement import EvaluationEvent, FeatureFlag, Variant, VariantAssignmentReason
import featuremanagement.opentelemetry._send_telemetry


@pytest.mark.usefixtures("caplog")
class TestSendTelemetryAppinsights:

    def test_send_telemetry_appinsights(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED

        with patch("featuremanagement.opentelemetry._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.opentelemetry._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert mock_track_event.call_args[0][1]["Variant"] == "TestVariant"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "DefaultWhenDisabled"

    def test_send_telemetry_appinsights_no_user(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = False
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED

        with patch("featuremanagement.opentelemetry._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.opentelemetry._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "False"
            assert "TargetingId" not in mock_track_event.call_args[0][1]
            assert mock_track_event.call_args[0][1]["Variant"] == "TestVariant"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "DefaultWhenDisabled"

    def test_send_telemetry_appinsights_no_variant(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"

        with patch("featuremanagement.opentelemetry._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.opentelemetry._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert "Variant" not in mock_track_event.call_args[0][1]
            assert "Reason" not in mock_track_event.call_args[0][1]

    def test_send_telemetry_open_telemetry(self, caplog):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        with patch.dict("sys.modules", {"azure.monitor.events.extension": None}):
            reload(sys.modules["featuremanagement.opentelemetry._send_telemetry"])
            with patch("featuremanagement.opentelemetry._send_telemetry._event_logger.info") as get_logger_mock:
                caplog.set_level(logging.WARNING)
                featuremanagement.opentelemetry._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                    evaluation_event
                )
                get_logger_mock.assert_called_once()
                assert get_logger_mock.call_args[0][0] == "FeatureEvaluation"
                assert get_logger_mock.call_args[1]["extra"]["FeatureName"] == "TestFeature"
                assert get_logger_mock.call_args[1]["extra"]["Enabled"] == "True"
                assert "TargetingId" not in get_logger_mock.call_args[1]["extra"]
                assert "Variant" not in get_logger_mock.call_args[1]["extra"]
                assert "VariantAssignmentReason" not in get_logger_mock.call_args[1]["extra"]
