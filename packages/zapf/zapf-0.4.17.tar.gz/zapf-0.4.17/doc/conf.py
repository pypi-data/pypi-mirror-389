# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath('..'))  # noqa: PTH100


# -- Project information -----------------------------------------------------

project = 'Zapf'
author = 'Georg Brandl, Enrico Faulhaber'
copyright = '2021, ' + author  # noqa: A001

master_doc = 'index'
default_role = 'py:obj'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_logo = '_static/logo.png'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'logo_only': True,
}

autodoc_member_order = 'bysource'

intersphinx_mapping = {
    'pils': ('https://forge.frm2.tum.de/public/doc/plc/master/html', None),
}
