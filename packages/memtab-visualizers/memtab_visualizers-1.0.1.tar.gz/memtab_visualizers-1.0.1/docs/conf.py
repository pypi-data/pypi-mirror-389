# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import subprocess
import sys

project = "Memtab Visualizers"
copyright = "2025, Eaton Corporation"
author = "Dave VanKampen"

current_dir = os.path.dirname(__file__)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinxcontrib.apidoc",  # for automatic generation of .rst files from Python modules
    "sphinx.ext.autodoc",  # for automatic generation of documentation from docstrings (follows apidoc)
    "sphinx_autodoc_typehints",
    "sphinx_multiversion",
    "sphinxcontrib.mermaid",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_typehints_format = "short"
python_use_unqualified_type_names = True

autodoc_default_options = {"members": True, "undoc-members": True}

apidoc_module_dir = "../src"
apidoc_output_dir = current_dir
apidoc_separate_modules = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"

html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "versioning.html",
    ],
}


sys.path.insert(0, os.path.abspath("../src"))


source_path = os.path.normpath(os.path.join(current_dir, "..", "features"))
subprocess.run(
    [
        "sphinx-gherkindoc",
        source_path,
        current_dir,
        "--toc-name",
        "gherkin",
        "--maxtocdepth",
        "4",
    ]
)


# -- Sphinx-Multiversion Configuration ---------------------------------------
smv_branch_whitelist = r"^main$"  # Only the main branch
smv_tag_whitelist = r"^v?\d+\.\d+\.\d+$"  # Tags in the form X.Y.Z or vX.Y.Z
