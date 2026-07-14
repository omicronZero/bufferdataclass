import os
import sys
import tomllib
from typing import Any

import setuptools_scm

root_dir = '../..'

sys.path.insert(0, os.path.abspath(root_dir))

with open(os.path.join(root_dir, 'pyproject.toml'), 'rb') as stream:
    project_meta = tomllib.load(stream)


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


def extract_info(*path: str, default: str = '') -> Any:
    current = project_meta

    for p in path:
        if not hasattr(current, '__getitem__'):
            return default

        try:
            current = current[p]
        except KeyError:
            return default

    return current


# TODO: adjust copyright and optionally the other fields below. Use '\xa9' for the copyright sign
copyright = ''

project = extract_info('project', 'name')
authors = extract_info('project', 'authors')
author = ', '.join(auth['name'] for auth in authors if isinstance(auth, dict))
release = setuptools_scm.get_version(root_dir)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary']

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# change this to the respective sphinx template (original was 'alabaster')
# note that pydata requires `pip install pydata-sphinx-theme`. If you change the theme, change the
# `.github/workflows/check_and_deploy.yml` step for the theme setup accordingly
html_theme = 'pydata_sphinx_theme'
# html_static_path = ['_static']
