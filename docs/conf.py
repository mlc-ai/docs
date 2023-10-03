# pylint: disable=invalid-name, exec-used, redefined-builtin
# -*- coding: utf-8 -*-
import inspect
import os
from functools import partial
from hashlib import md5
from importlib import import_module
from pathlib import Path
import re
from typing import List
from unittest.mock import patch

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
home_path = os.path.join(home_path, "docs")

version = tvm.__version__
release = version

extensions = [
    "sphinx_gallery.gen_gallery",
    "sphinx_tabs.tabs",
    "sphinx_toolbox.collapse",
    "sphinxcontrib.httpdomain",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]

source_suffix = [".rst"]

language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# This line is used for bypass the issue of sidebar toc
exclude_patterns.append("**/tutorials/index.rst")
exclude_patterns.append("**/tutorials/README.rst")

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for customization --------------------------------------------


def monkey_patch(module_name, func_name):
    """Helper function for monkey-patching library functions.

    Used to modify a few sphinx-gallery behaviors to make the "Open in Colab" button work correctly.
    Should be called as a decorator with arguments. Note this behaves differently from unittest's
    @mock.patch, as our monkey_patch decorator should be placed on the new version of the function.
    """
    module = import_module(module_name)
    original_func = getattr(module, func_name)

    def decorator(function):
        updated_func = partial(function, real_func=original_func)
        setattr(module, func_name, updated_func)
        return updated_func

    return decorator


# -- Options for Colab integration --------------------------------------------

CURRENT_FILE_CONF = None


@monkey_patch("sphinx_gallery.py_source_parser", "split_code_and_text_blocks")
def split_code_and_text_blocks(source_file, real_func, return_node=False):
    """Monkey-patch split_code_and_text_blocks to expose sphinx-gallery's file-level config.

    It's kinda gross, but we need access to file_conf to detect the requires_cuda flag.
    """
    global CURRENT_FILE_CONF

    res = real_func(source_file, return_node)
    CURRENT_FILE_CONF = res[0]
    return res


# This header replaces the default sphinx-gallery one in sphinx_gallery/gen_rst.py.
COLAB_HTML_HEADER = """
.. DO NOT EDIT. THIS FILE WAS AUTOMATICALLY GENERATED BY
.. TVM'S MONKEY-PATCHED VERSION OF SPHINX-GALLERY. TO MAKE
.. CHANGES, EDIT THE SOURCE PYTHON FILE:
.. "{python_file}"

.. only:: html

    .. note::
        :class: sphx-glr-download-link-note

        This tutorial can be used interactively with Google Colab! You can also click
        :ref:`here <sphx_glr_download_{ref_name}>` to run the Jupyter notebook locally.

        .. image:: {button_svg}
            :align: center
            :target: {colab_url}
            :width: 300px

.. rst-class:: sphx-glr-example-title

.. _sphx_glr_{ref_name}:

"""

# Google Colab allows opening .ipynb files on GitHub by appending a GitHub path to this base URL.
COLAB_URL_BASE = "https://colab.research.google.com/github"
# The GitHub path where the site is automatically deployed by tvm-bot.
IPYTHON_GITHUB_BASE = "mlc-ai/docs/blob/gh-pages/_downloads/"
# The SVG image of the "Open in Colab" button.
BUTTON = (
    "https://raw.githubusercontent.com/tlc-pack/web-data/main/images/utilities/colab_button.svg"
)


@monkey_patch("sphinx_gallery.gen_rst", "save_rst_example")
def save_rst_example(
    example_rst,
    example_file,
    time_elapsed,
    memory_used,
    gallery_conf,
    real_func,
):
    """Monkey-patch save_rst_example to include the "Open in Colab" button."""

    # The url is the md5 hash of the notebook path.
    example_fname = os.path.relpath(example_file, gallery_conf["src_dir"])
    ref_fname = example_fname.replace(os.path.sep, "_")
    notebook_path = example_fname[:-2] + "ipynb"
    digest = md5(notebook_path.encode()).hexdigest()

    # Fixed documentation versions must link to different (earlier) .ipynb notebooks.
    colab_url = f"{COLAB_URL_BASE}/{IPYTHON_GITHUB_BASE}"
    if "dev" not in version:
        colab_url += version + "/"
    colab_url += digest + "/" + os.path.basename(notebook_path)

    new_header = COLAB_HTML_HEADER.format(
        python_file=example_fname,
        ref_name=ref_fname,
        colab_url=colab_url,
        button_svg=BUTTON,
    )
    with patch("sphinx_gallery.gen_rst.EXAMPLE_HEADER", new_header):
        real_func(example_rst, example_file, time_elapsed, memory_used, gallery_conf)


INSTALL_TVM_UNITY_DEV = """
%%shell
# Installs the nightly dev build of Apache TVM Unity from PyPI. If you wish to build
# from source, see https://mlc.ai/docs/get_started/install.html#option-2-build-from-source
pip install mlc-ai-nightly --pre -f https://mlc.ai/wheels"""

INSTALL_TVM_UNITY_CUDA_DEV = """\
%%shell
# Installs the nightly dev build of Apache TVM Unity from PyPI, with CUDA enabled.
# To use this, you must request a Google Colab instance with a GPU by going to Runtime ->
# Change runtime type -> Hardware accelerator -> GPU.
# If you wish to build from source, see see
# https://mlc.ai/docs/get_started/install.html#option-2-build-from-source
pip install mlc-ai-nightly-cu118 --pre -f https://mlc.ai/wheels"""


@monkey_patch("sphinx_gallery.gen_rst", "jupyter_notebook")
def jupyter_notebook(script_blocks, gallery_conf, target_dir, real_func):
    """Monkey-patch sphinx-gallery to add a TVM import block to each IPython notebook.

    If we had only one import block, we could skip the patching and just set first_notebook_cell.
    However, how we import TVM depends on if we are using a fixed or dev version, and whether we
    will use the GPU.

    Tutorials requiring a CUDA-enabled build of TVM should use the flag:
    # sphinx_gallery_requires_cuda = True
    """

    requires_cuda = CURRENT_FILE_CONF.get("requires_cuda", False)

    new_conf = {
        **gallery_conf,
        "first_notebook_cell": INSTALL_TVM_UNITY_CUDA_DEV
        if requires_cuda
        else INSTALL_TVM_UNITY_DEV,
    }
    return real_func(script_blocks, new_conf, target_dir)


# -- Options for HTML output ----------------------------------------------


def fixup_tutorials(original_url: str) -> str:
    if "tutorials" in original_url:
        # The `index.rst` is omitted from the URL in the sidebar
        assert not original_url.endswith("index.rst")
        return re.sub(r"tutorials/(.*)\.rst", "tutorials/\\1.py", original_url)
    else:
        # do nothing for normal non-tutorial .rst files
        return original_url


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
    "edit_link_hook_fn": fixup_tutorials,
    # "header_logo": "/path/to/logo",
    # "header_logo_link": "",
    # "version_selecter": "",
}


# add additional overrides
templates_path += [tlcpack_sphinx_addon.get_templates_path()]
html_static_path += [tlcpack_sphinx_addon.get_static_path()]


# Sphinx-Gallery Settings
examples_dirs = [
    f"{home_path}/get_started/tutorials",
    f"{home_path}/deep_dive/tensor_ir/tutorials/",
]

gallery_dirs = [
    "get_started/tutorials/",
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

# -- Options for Autodoc ----------------------------------------------

add_module_names = True
autodoc_default_options = {
    "member-order": "alphabetical",
}

tvm_class_name_rewrite_map = {
    "tvm.tir": ["Var", "Call"],
    "tvm.relax": ["Var", "Call"],
    "tvm.relax.frontend.nn": ["Module"],
}


def distinguish_class_name(name: str, lines: List[str]):
    """Distinguish the docstring of type annotations.

    In the whole TVM, there are many classes with the same name but in different modules,
    e.g. ``tir.Var``, ``relax.Var``. This function is used to distinguish them in the docstring,
    by adding the module name as prefix.

    To be specific, this function will check the current object name, and if it in the specific
    module with specific name, it will add the module name as prefix to the class name to prevent
    the confusion. Further, we only add the prefix to those standalone class name, but skip
    the pattern of `xx.Var`, `Var.xx` and `xx.Var.xx`.

    Parameters
    ----------
    name : str
        The full name of the object in the doc.

    lines : list
        The docstring lines, need to be modified inplace.
    """
    remap = {}
    for module_name in tvm_class_name_rewrite_map:
        if name.startswith(module_name):
            short_name = module_name[4:] if module_name.startswith("tvm.") else module_name
            for class_name in tvm_class_name_rewrite_map[module_name]:
                remap.update({class_name: f"{short_name}.{class_name}"})

    for k, v in remap.items():
        for i in range(len(lines)):
            lines[i] = re.sub(rf"(?<!\.)\b{k}\b(?!\.)", v, lines[i])


def process_docstring(app, what, name, obj, options, lines):
    """Sphinx callback to process docstring"""
    if callable(obj) or inspect.isclass(obj):
        distinguish_class_name(name, lines)


def setup(app):
    app.connect("autodoc-process-docstring", process_docstring)