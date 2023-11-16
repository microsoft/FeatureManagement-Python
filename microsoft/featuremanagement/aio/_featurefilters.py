# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from abc import ABC, abstractmethod
from .._featurefilters import FeatureFilter as FF


class FeatureFilter(FF):
    """
    Parent class for all Async feature filters
    """

    @abstractmethod
    async def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context
        :param Mapping context: Context for the feature flag
        :paramtype context: Mapping
        """
