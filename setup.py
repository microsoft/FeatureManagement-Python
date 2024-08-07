#!/usr/bin/env python

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import re
import os.path
from io import open
from setuptools import find_packages, setup

# Change the PACKAGE_NAME only to change folder and different name
PACKAGE_NAME = "featuremanagement"
PACKAGE_PPRINT_NAME = "Feature Management"

# a-b-c => a/b/c
package_folder_path = PACKAGE_NAME.replace("-", "/")
# a-b-c => a.b.c
namespace_name = PACKAGE_NAME.replace("-", ".")

# Version extraction inspired from 'requests'
with open(os.path.join(package_folder_path, "_version.py"), "r") as fd:
    version = re.search(r'^VERSION\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("Cannot find version information")

with open("README.md", encoding="utf-8") as f:
    readme = f.read()
with open("CHANGELOG.md", encoding="utf-8") as f:
    changelog = f.read()

setup(
    name=PACKAGE_NAME,
    version=version,
    include_package_data=True,
    description="Microsoft {} Library for Python".format(PACKAGE_PPRINT_NAME),
    long_description=readme + "\n\n" + changelog,
    long_description_content_type="text/markdown",
    author="Microsoft Corporation",
    author_email="appconfig@microsoft.com",
    url="https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/appconfiguration/feature-management",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    zip_safe=False,
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[],
    extras_require={
        "AzureMonitor": ["azure-monitor-events-extension<2.0.0"],
    },
)
