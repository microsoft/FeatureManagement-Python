# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------


class Variant:
    """
    A class representing a variant configuration assigned by a feature flag.

    :param name: The name of the variant
    :type name: str
    :param configuration: The configuration of the variant
    :type configuration: dict
    """

    def __init__(self, name, configuration):
        self._name = name
        self._configuration = configuration

    @property
    def name(self):
        """
        The name of the variant
        :rtype: str
        """
        return self._name

    @property
    def configuration(self):
        """
        The configuration of the variant
        :rtype: dict
        """
        return self._configuration
