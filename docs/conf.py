import importlib
from datetime import date

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
html_static_path = ["_static"]
html_css_files = ["style.css"]
html_logo = "_static/logo_capella.png"


html_theme_options = {
    "navigation_depth": 3,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_member_order = "alphabetical"
