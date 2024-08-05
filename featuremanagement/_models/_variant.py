# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from typing import Any


class Variant:
    """
    A class representing a variant configuration assigned by a feature flag.

    :param str name: The name of the variant
    :param dict configuration: The configuration of the variant.
    """

    def __init__(self, name: str, configuration: Any) -> None:
        self._name = name
        self._configuration = configuration

    @property
    def name(self) -> str:
        """
        The name of the variant.
        :rtype: str
        """
        return self._name

    @property
    def configuration(self) -> Any:
        """
        The configuration of the variant.
        :rtype: Any
        """
        return self._configuration
