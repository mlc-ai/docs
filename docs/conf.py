# pylint: disable=invalid-name, exec-used, redefined-builtin
# -*- coding: utf-8 -*-
import os
from pathlib import Path

import sphinx_rtd_theme
import tlcpack_sphinx_addon
import tvm

# -- General configuration ------------------------------------------------

# General information about the project.

project = "Apache TVM Unity"
author = "Apache Software Foundation"
copyright = f"2020 - 2023, {author}"
github_doc_root = "https://github.com/mlc-ai/docs/"

# Version information.
curr_path = Path(__file__).expanduser().absolute().parent
# Can't use curr_path.parent, because sphinx_gallery requires a relative path.
home_path = Path(os.pardir, os.pardir) if "_staging" in str(curr_path) else Path(os.pardir)

version = tvm.__version__
release = version

extensions = [
    "sphinx_gallery.gen_gallery",
    "sphinx_tabs.tabs",
    "sphinx_toolbox.collapse",
    "sphinxcontrib.httpdomain",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

source_suffix = [".rst"]

language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# This line is used for bypass the issue of sidebar toc
exclude_patterns.append("**/tutorials/index.rst")

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

# The theme is set by the make target

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

templates_path = []

html_static_path = []

footer_copyright = "© 2023 Apache Software Foundation | All rights reserved"
footer_note = " ".join(
    """
Copyright © 2023 The Apache Software Foundation. Apache TVM, Apache, the Apache feather,
and the Apache TVM project logo are either trademarks or registered trademarks of
the Apache Software Foundation.""".split(
        "\n"
    )
).strip()

header_logo = "https://tvm.apache.org/assets/images/logo.svg"
html_logo = "_static/img/tvm-logo-small.png"
html_favicon = "_static/img/tvm-logo-square.png"

html_theme_options = {
    "logo_only": True,
}

header_links = [
    ("Github", "https://github.com/apache/tvm/tree/unity/"),
    ("MLC-LLM", "https://mlc.ai/mlc-llm/"),
    ("MLC-Tutorial", "https://mlc.ai/"),
]

header_dropdown = {
    "name": "ASF",
    "items": [
        ("Apache Homepage", "https://apache.org/"),
        ("License", "https://www.apache.org/licenses/"),
        ("Sponsorship", "https://www.apache.org/foundation/sponsorship.html"),
        ("Security", "https://www.apache.org/security/"),
        ("Thanks", "https://www.apache.org/foundation/thanks.html"),
        ("Events", "https://www.apache.org/events/current-event"),
    ],
}

html_context = {
    "footer_copyright": footer_copyright,
    "footer_note": footer_note,
    "header_links": header_links,
    "header_dropdown": header_dropdown,
    "display_github": True,
    "github_user": "mlc-ai",
    "github_repo": "docs",
    "github_version": "main/docs/",
    "theme_vcs_pageview_mode": "edit",
    # "edit_link_hook_fn": fixup_tutorials,
    # "header_logo": "/path/to/logo",
    # "header_logo_link": "",
    # "version_selecter": "",
}


# add additional overrides
templates_path += [tlcpack_sphinx_addon.get_templates_path()]
html_static_path += [tlcpack_sphinx_addon.get_static_path()]


# Sphinx-Gallery Settings
examples_dirs = [
    f"{home_path}/tutorials/contribute/",
    f"{home_path}/tutorials/get_started/",
    f"{home_path}/tutorials/deep_dive/tensor_ir/",
]

gallery_dirs = [
    "tutorials/contribute/",
    "tutorials/get_started/",
    "deep_dive/tensor_ir/tutorials/",
]

sphinx_gallery_conf = {
    "examples_dirs": examples_dirs,
    "gallery_dirs": gallery_dirs,
    "backreferences_dir": "gen_modules/backreferences",
    "filename_pattern": r".*\.py",
    "ignore_pattern": r"__init__\.py",
    "show_signature": False,
    "download_all_examples": False,
    "promote_jupyter_magic": True,
}
