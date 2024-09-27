# Configuration file for the Sphinx documentation builder.
#

import os
import sys
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath("../featuremanagement"))

project = "FeatureManagement"
copyright = "2024, Microsoft"
author = "Microsoft"
release = "2.0.0b2"

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx_toolbox.more_autodoc.autonamedtuple",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------\

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]
