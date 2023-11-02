# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from abc import ABC, abstractmethod


class FeatureFilter(ABC):
    """
    Parent class for all feature filters
    """

    @abstractmethod
    async def evaluate(self, context, **kwargs):
        """
        Determine if the feature flag is enabled for the given context
        :param Mapping context: Context for the feature flag
        :paramtype context: Mapping
        """

    @property
    def name(self):
        """
        Get the name of the filter
        :return: Name of the filter, or alias if it exists
        :rtype: str
        """
        if hasattr(self, "_alias"):
            return self._alias
        return self.__class__.__name__

    def alias(alias):
        def wrapper(self):
            self._alias = alias
            return self

        return wrapper
