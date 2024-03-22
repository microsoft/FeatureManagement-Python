# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from tests.validation_tests.load_feature_flags import LoadFeatureFlagsFromFile
import unittest


class TestRequirementTypeFromFile(LoadFeatureFlagsFromFile, unittest.TestCase):
    # method: is_enabled
    def test_requirement_type_any(self):
        feature_manager = self.load_from_file("RequirementType.sample.json")

        # Feature Flag with two feature filters, the first is true, second is false, so the flag is enabled.
        assert feature_manager.is_enabled("FirstOrFeatureFlag")

        # Feature Flag with two feature filters, the first is false, second is true, so the flag is enabled.
        assert feature_manager.is_enabled("SecondOrFeatureFlag")

        # Feature Flag with two feature filters, same as Kappa, but specifies the requirement type.
        assert feature_manager.is_enabled("FristRequirementTypeAnyFeatureFlag")

        # Feature Flag with two feature filters, same as Lambda, but both filters are false, so the flag is disabled.
        assert not feature_manager.is_enabled("SecondtRequirementTypeAnyFeatureFlag")

    # method: is_enabled
    def test_requirement_type_all(self):
        feature_manager = self.load_from_file("RequirementType.sample.json")

        # Feature Flag with two feature filters with the All requirement type, the first is true, second is false, so the flag is disabled.
        assert not feature_manager.is_enabled("TrueRequirementTypeAllFeatureFlag", user="Adam")

        # Feature Flag with two feature filters with the All requirement type, both are true, so the flag is enabled.
        assert feature_manager.is_enabled("FalseRequirementTypeAllFeatureFlag", user="Adam")
