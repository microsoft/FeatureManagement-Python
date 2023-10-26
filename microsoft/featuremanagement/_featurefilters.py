# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------


class FeatureFilter:
    """
    Parent class for all feature filters
    """

    def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context
        :param Mapping context: Context for the feature flag
        :paramtype context: Mapping
        """
