# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Mapping, Callable, Any, Optional


class FeatureFilter(ABC):
    """
    Parent class for all feature filters.
    """

    _alias: Optional[str] = None

    @abstractmethod
    def evaluate(self, context: Mapping[Any, Any], **kwargs: Any) -> bool:
        """
        Determine if the feature flag is enabled for the given context.

        :param Mapping context: Context for the feature flag.
        """

    @property
    def name(self) -> str:
        """
        Get the name of the filter.

        :return: Name of the filter, or alias if it exists.
        :rtype: str
        """
        if hasattr(self, "_alias") and self._alias:
            return self._alias
        return self.__class__.__name__

    @staticmethod
    def alias(alias: str) -> Callable[..., Any]:
        """
        Decorator to set the alias for the filter.

        :param str alias: Alias for the filter.
        :return: Decorator.
        :rtype: Callable
        """

        def wrapper(cls: "FeatureFilter") -> Any:
            cls._alias = alias  # pylint: disable=protected-access
            return cls

        return wrapper
