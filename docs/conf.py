import importlib
from datetime import date

# import os
# import toml
# from pathlib import Path

# pyproject = toml.load(Path(__file__).parent.parent / "pyproject.toml")
# __version__ = pyproject["tool"]["poetry"]["version"]

project = "capella-console-client"
__version__ = importlib.metadata.version(project)

author = "Capella Space"
copyright = f"{date.today().year}, {author}"

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
html_static_path = []
html_logo = "logo_capella.png"


html_theme_options = {
    "navigation_depth": 2,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_member_order = "alphabetical"
