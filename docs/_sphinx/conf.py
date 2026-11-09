# ------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -------------------------------------------------------------------------
"""Shared rendering configuration for tagged release documentation."""

from typing import Any

from sphinx.application import Sphinx

project = "FeatureManagement"
copyright = "2024, Microsoft"
author = "Microsoft"
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_toolbox.more_autodoc.autonamedtuple",
    "sphinxcontrib.jquery",
]
html_theme = "sphinx_rtd_theme"
html_static_path: list[str] = []
html_theme_path: list[str] = []


def format_release_docstrings(_app: Sphinx, _what: str, name: str, _obj: Any, _options: Any, lines: list[str]) -> None:
    """Indent historical keyword-field continuations without modifying release source."""
    if name not in ("featuremanagement.FeatureManager", "featuremanagement.aio.FeatureManager"):
        return
    for index, line in enumerate(lines):
        if line in ("evaluated.", "context if one isn't provided."):
            lines[index] = "    " + line


def setup(app: Sphinx) -> dict[str, bool]:
    """Register documentation-only rendering corrections."""
    app.connect("autodoc-process-docstring", format_release_docstrings)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
