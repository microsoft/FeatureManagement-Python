# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Tests for Application Insights telemetry publishing."""

import logging
from unittest.mock import patch
import pytest
from featuremanagement import EvaluationEvent, FeatureFlag, Variant, VariantAssignmentReason, TargetingContext
import featuremanagement.azuremonitor._send_telemetry
from featuremanagement.azuremonitor import TargetingSpanProcessor


def _event_properties(mock_track_event):
    return mock_track_event.call_args.kwargs["event_properties"]


@pytest.mark.usefixtures("caplog")
class TestSendTelemetryAppinsights:

    user_id = None

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

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1] == "test_user"
            event_properties = _event_properties(mock_track_event)
            assert event_properties["FeatureName"] == "TestFeature"
            assert event_properties["Enabled"] == "True"
            assert event_properties["Variant"] == "TestVariant"
            assert event_properties["ETag"] == "cmwBRcIAq1jUyKL3Kj8bvf9jtxBrFg-R-ayExStMC90"
            assert (
                event_properties["FeatureFlagReference"]
                == "fake-store-uri/kv/.appconfig.featureflag/TestFeature"
            )
            assert event_properties["FeatureFlagId"] == "fake-feature-flag-id"

    def test_track_event_preserves_reserved_custom_event_name(self):
        with patch("featuremanagement.azuremonitor._send_telemetry._initialize_event_logger"), patch(
            "featuremanagement.azuremonitor._send_telemetry._event_logger.info"
        ) as mock_event_logger_info, patch(
            "featuremanagement.azuremonitor._send_telemetry.HAS_OPENTELEMETRY_LOGGING", True
        ):
            featuremanagement.azuremonitor._send_telemetry.track_event(
                "FeatureEvaluation",
                "test_user",
                {
                    "microsoft.custom_event.name": "override_attempt",
                    "CustomProperty": "custom_value",
                },
            )

            mock_event_logger_info.assert_called_once()
            assert mock_event_logger_info.call_args[0][0] == "FeatureEvaluation"
            assert mock_event_logger_info.call_args.kwargs["extra"]["microsoft.custom_event.name"] == "FeatureEvaluation"
            assert mock_event_logger_info.call_args.kwargs["extra"]["CustomProperty"] == "custom_value"
            assert mock_event_logger_info.call_args.kwargs["extra"]["TargetingId"] == "test_user"

    def test_send_telemetry_appinsights_no_user(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        variant = Variant("TestVariant", None)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = False
        evaluation_event.variant = variant
        evaluation_event.reason = VariantAssignmentReason.DEFAULT_WHEN_DISABLED

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1] == ""
            event_properties = _event_properties(mock_track_event)
            assert event_properties["FeatureName"] == "TestFeature"
            assert event_properties["Enabled"] == "False"
            assert "TargetingId" not in event_properties
            assert event_properties["Variant"] == "TestVariant"
            assert event_properties["VariantAssignmentReason"] == "DefaultWhenDisabled"

    def test_send_telemetry_appinsights_no_variant(self):
        feature_flag = FeatureFlag.convert_from_json({"id": "TestFeature"})
        evaluation_event = EvaluationEvent(feature_flag)
        evaluation_event.feature = feature_flag
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1] == "test_user"
            event_properties = _event_properties(mock_track_event)
            assert event_properties["FeatureName"] == "TestFeature"
            assert event_properties["Enabled"] == "True"
            assert "Variant" not in event_properties
            assert "Reason" not in event_properties

    def test_send_telemetry_appinsights_no_feature_flag(self):
        evaluation_event = EvaluationEvent(None)
        evaluation_event.enabled = True
        evaluation_event.user = "test_user"

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
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

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1] == "test_user"
            event_properties = _event_properties(mock_track_event)
            assert event_properties["FeatureName"] == "TestFeature"
            assert event_properties["Enabled"] == "True"
            assert event_properties["Variant"] == "big"
            assert event_properties["VariantAssignmentReason"] == "DefaultWhenEnabled"

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

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1] == "test_user"
            event_properties = _event_properties(mock_track_event)
            assert event_properties["FeatureName"] == "TestFeature"
            assert event_properties["Enabled"] == "True"
            assert event_properties["Variant"] == "big"
            assert event_properties["VariantAssignmentReason"] == "DefaultWhenEnabled"

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

        with patch("featuremanagement.azuremonitor._send_telemetry.track_event") as mock_track_event:
            # This is called like this so we can override the track_event function
            featuremanagement.azuremonitor._send_telemetry.publish_telemetry(  # pylint: disable=protected-access
                evaluation_event
            )
            mock_track_event.assert_called_once()
            assert mock_track_event.call_args[0][0] == "FeatureEvaluation"
            assert mock_track_event.call_args[0][1] == "test_user"
            event_properties = _event_properties(mock_track_event)
            assert event_properties["FeatureName"] == "TestFeature"
            assert event_properties["Enabled"] == "True"
            assert event_properties["Variant"] == "big"
            assert event_properties["VariantAssignmentReason"] == "Percentile"
            assert event_properties["VariantAssignmentPercentage"] == "25"
            assert "DefaultWhenEnabled" not in event_properties

    def test_targeting_span_processor(self, caplog):
        processor = TargetingSpanProcessor()
        processor.on_start(None)
        assert "" in caplog.text
        caplog.clear()

        processor = TargetingSpanProcessor(targeting_context_accessor="not callable")
        processor.on_start(None)
        assert "" in caplog.text
        caplog.clear()

        processor = TargetingSpanProcessor(targeting_context_accessor=self.bad_targeting_context_accessor)
        processor.on_start(None)
        assert (
            "targeting_context_accessor did not return a TargetingContext. Received type <class 'str'>." in caplog.text
        )
        caplog.clear()

        processor = TargetingSpanProcessor(targeting_context_accessor=self.async_targeting_context_accessor)
        processor.on_start(None)
        assert "Async targeting_context_accessor is not supported." in caplog.text
        caplog.clear()

        processor = TargetingSpanProcessor(targeting_context_accessor=self.accessor_callback)
        logging.getLogger().setLevel(logging.DEBUG)
        processor.on_start(None)
        assert "TargetingContext does not have a user ID." in caplog.text
        caplog.clear()

        with patch("opentelemetry.sdk.trace.Span") as mock_span:
            self.user_id = "test_user"
            processor.on_start(mock_span)
            assert mock_span.set_attribute.call_args[0][0] == "TargetingId"
            assert mock_span.set_attribute.call_args[0][1] == "test_user"

        self.user_id = None

    def bad_targeting_context_accessor(self):
        return "not targeting context"

    async def async_targeting_context_accessor(self):
        return TargetingContext(user_id=self.user_id)

    def accessor_callback(self):
        return TargetingContext(user_id=self.user_id)
