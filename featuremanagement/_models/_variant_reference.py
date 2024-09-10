# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
from dataclasses import dataclass
from typing import Optional, Mapping, Any
from ._constants import VARIANT_REFERENCE_NAME, CONFIGURATION_VALUE, STATUS_OVERRIDE


@dataclass
class VariantReference:
    """
    Represents a variant reference.
    """

    def __init__(self) -> None:
        self._name = None
        self._configuration_value = None
        self._status_override = None

    @classmethod
    def convert_from_json(cls, json: Mapping[str, Any]) -> "VariantReference":
        """
        Convert a JSON object to VariantReference.

        :param dict json: JSON object
        :return: VariantReference
        :rtype: VariantReference
        """
        variant_reference = cls()
        variant_reference._name = json.get(VARIANT_REFERENCE_NAME)
        variant_reference._configuration_value = json.get(CONFIGURATION_VALUE)
        variant_reference._status_override = json.get(STATUS_OVERRIDE, None)
        return variant_reference

    @property
    def name(self) -> Optional[str]:
        """
        Get the name of the variant.

        :return: Name of the variant
        :rtype: str
        """
        return self._name

    @property
    def configuration_value(self) -> Optional[str]:
        """
        Get the configuration value for the variant.

        :return: Configuration value for the variant.
        :rtype: str
        """
        return self._configuration_value

    @property
    def status_override(self) -> Optional[str]:
        """
        Get the status override for the variant.

        :return: Status override for the variant.
        :rtype: str
        """
        return self._status_override
