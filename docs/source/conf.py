# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from urwidgets import __version__

# -- Project information -----------------------------------------------------
project = "urWIDgets"
copyright = "2023, Toluwaleke Ogundipe"
author = "Toluwaleke Ogundipe"
release = __version__

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_toolbox.github",
    "sphinx_toolbox.sidebar_links",
    "sphinx_toolbox.more_autosummary",
]

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"

# -- Options for extensions ----------------------------------------------

# # -- sphinx-autodoc -----------------------------------------------------
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "member-order": "bysource",
    "autosummary": True,
    "autosummary-nosignatures": True,
}
autodoc_typehints = "description"
autodoc_typehints_format = "fully-qualified"
autodoc_typehints_description_target = "documented"
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = False

# # -- sphinx-intersphinx ----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "urwid": ("https://urwid.org", None),
}

# # -- sphinx_toolbox-github ----------------------------------------------
github_username = "AnonymouX47"
github_repository = "urwidgets"

# # -- sphinx_toolbox-more_autosummary ----------------------------------------------
autodocsumm_member_order = "bysource"
