# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
import random
from featuremanagement import FeatureFilter


@FeatureFilter.alias("Sample.Random")
class RandomFilter(FeatureFilter):
    """
    A sample feature filter that enables the feature for a random percentage of users.
    """

    def evaluate(self, context, **kwargs):
        """Determine if the feature flag is enabled for the given context"""
        value = context.get("parameters", {}).get("Value", 0)
        if value < random.randint(0, 100):
            return True
        return False
