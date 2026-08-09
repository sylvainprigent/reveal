from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC))

project = "Reveal"
copyright = "2026, Reveal"
author = "Sylvain M. Prigent"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "furo"

autodoc_typehints = "description"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
