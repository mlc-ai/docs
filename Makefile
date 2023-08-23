# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= python -m sphinx
SOURCEDIR     = docs
BUILDDIR      = _build
STAGINGDIR    = _staging

.PHONY: help Makefile

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
# %: Makefile
# 	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf $(BUILDDIR)
	rm -rf $(STAGINGDIR)

staging:
	# Prepare the staging directory. Sphinx gallery automatically
	# writes new .rst files into the current directory. This can
	# cause issues when switching branches. By sequestering the
	# auto-generated files into the staging directory, they can be
	# removed without knowing the exact directory.

	mkdir -p $(STAGINGDIR)

	# Remove any symlinks that currently exist
	find $(STAGINGDIR) -type l -exec rm {} \;

	# Reproduce the directory structure
	find ${SOURCEDIR} \
	      -path ./$(BUILDDIR) -prune -o -path ./$(STAGINGDIR) -prune -o \
	      -name "*.rst"  \
	      -printf "$(STAGINGDIR)/%h\n" \
              | sort | uniq | xargs mkdir -p

	# Symlink all .rst files into the staging directory
	find ${SOURCEDIR} \
	      -path ./$(BUILDDIR) -prune -o -path ./$(STAGINGDIR) -prune -o \
	      -name "*.rst"  \
	      -exec ln -s $(PWD)/{} $(STAGINGDIR)/{} \;

	ln -s $(PWD)/$(SOURCEDIR)/conf.py $(STAGINGDIR)/${SOURCEDIR}/conf.py
	ln -s $(PWD)/$(SOURCEDIR)/_static $(STAGINGDIR)/${SOURCEDIR}/_static

html: staging
	$(SPHINXBUILD) -M html $(STAGINGDIR)/docs $(BUILDDIR)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)."