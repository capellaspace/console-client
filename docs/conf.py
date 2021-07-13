import json
import os
import sys
import traceback

sys.path.insert(0, os.path.abspath("../"))
from capella_console_client.version import __version__

project = "capella-console-client"
copyright = "2021, Capella Space"
author = "Capella Space"

version = __version__
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
]


autodoc_typehints = "description"

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = "logo_capella.png"


html_theme_options = {
    "navigation_depth": 2,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_member_order = "alphabetical"
