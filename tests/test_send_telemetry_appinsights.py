# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from unittest.mock import patch
import pytest
from featuremanagement import EvaluationEvent, FeatureFlag, Variant, VariantAssignmentReason
import featuremanagement.azuremonitor._send_telemetry


@pytest.mark.usefixtures("caplog")
class TestSendTelemetryAppinsights:

    def test_send_telemetry_appinsights(self):
        feature_flag = FeatureFlag.convert_from_json(
            {
                "id": "TestFeature",
                "telemetry": {
                    "enabled": True,
                    "metadata": {
                        "ETag": "cmwBRcIAq1jUyKL3Kj8bvf9jtxBrFg-R-ayExStMC90",
                        "FeatureFlagReference": "fake-store-uri/kv/.appconfig.featureflag/TestFeature",
                        "FeatureFlagId": "fake-feature-flag-id",
                        "AllocationId": "fake-allocation-id",
                    },
                },
            }
        )
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert mock_track_event.call_args[0][1]["Variant"] == "TestVariant"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "DefaultWhenDisabled"
            assert "VariantAssignmentPercentage" not in mock_track_event.call_args[0][1]
            assert mock_track_event.call_args[0][1]["ETag"] == "cmwBRcIAq1jUyKL3Kj8bvf9jtxBrFg-R-ayExStMC90"
            assert (
                mock_track_event.call_args[0][1]["FeatureFlagReference"]
                == "fake-store-uri/kv/.appconfig.featureflag/TestFeature"
            )
            assert mock_track_event.call_args[0][1]["FeatureFlagId"] == "fake-feature-flag-id"
            assert mock_track_event.call_args[0][1]["AllocationId"] == "fake-allocation-id"
            assert "DefaultWhenEnabled" not in mock_track_event.call_args[0][1]

    def test_send_telemetry_appinsights_no_user(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = False
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "False"
            assert "TargetingId" not in mock_track_event.call_args[0][1]
            assert mock_track_event.call_args[0][1]["Variant"] == "TestVariant"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "DefaultWhenDisabled"
            assert "VariantAssignmentPercentage" not in mock_track_event.call_args[0][1]
            assert "DefaultWhenEnabled" not in mock_track_event.call_args[0][1]

    def test_send_telemetry_appinsights_no_variant(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert "Variant" not in mock_track_event.call_args[0][1]
            assert "Reason" not in mock_track_event.call_args[0][1]

    def test_send_telemetry_appinsights_no_feature_flag(self):
        evaluation_event = EvaluationEvent(None)
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_not_called()

    def test_send_telemetry_appinsights_default_when_enabled(self):
        feature_flag = FeatureFlag.convert_from_json(
            {
                "id": "TestFeature",
                "allocation": {
                    "default_when_enabled": "big",
                    "percentile": [{"from": 0, "to": 25, "variant": "big"}, {"from": 25, "to": 75, "variant": "small"}],
                },
            }
        )
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("big", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_ENABLED

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert mock_track_event.call_args[0][1]["Variant"] == "big"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "DefaultWhenEnabled"
            assert mock_track_event.call_args[0][1]["VariantAssignmentPercentage"] == "25"
            assert "DefaultWhenEnabled" in mock_track_event.call_args[0][1]
            assert mock_track_event.call_args[0][1]["DefaultWhenEnabled"] == "big"

    def test_send_telemetry_appinsights_default_when_enabled_no_percentile(self):
        feature_flag = FeatureFlag.convert_from_json(
            {
                "id": "TestFeature",
                "allocation": {
                    "default_when_enabled": "big",
                },
            }
        )
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("big", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_ENABLED

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert mock_track_event.call_args[0][1]["Variant"] == "big"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "DefaultWhenEnabled"
            assert mock_track_event.call_args[0][1]["VariantAssignmentPercentage"] == "100"
            assert "DefaultWhenEnabled" in mock_track_event.call_args[0][1]
            assert mock_track_event.call_args[0][1]["DefaultWhenEnabled"] == "big"

    def test_send_telemetry_appinsights_allocation(self):
        feature_flag = FeatureFlag.convert_from_json(
            {
                "id": "TestFeature",
                "allocation": {
                    "percentile": [{"from": 0, "to": 25, "variant": "big"}, {"from": 25, "to": 75, "variant": "small"}]
                },
            }
        )
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("big", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.PERCENTILE

        with patch("featuremanagement.azuremonitor._send_telemetry.azure_monitor_track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1]["FeatureName"] == "TestFeature"
            assert mock_track_event.call_args[0][1]["Enabled"] == "True"
            assert mock_track_event.call_args[0][1]["TargetingId"] == "test_user"
            assert mock_track_event.call_args[0][1]["Variant"] == "big"
            assert mock_track_event.call_args[0][1]["VariantAssignmentReason"] == "Percentile"
            assert mock_track_event.call_args[0][1]["VariantAssignmentPercentage"] == "25"
            assert "DefaultWhenEnabled" not in mock_track_event.call_args[0][1]
