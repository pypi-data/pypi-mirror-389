# docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
print(sys.path)


project = 'LocalSearch'
author = 'Rick Sanchez'
release = '0.1.0'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
templates_path = ['_templates']
exclude_patterns = []
html_show_sourcelink = True
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
