### Makefile for curry

PROGRAM = curry
PYTHON = python3
MANPAGE = data/curry.1
INSTALL_ARGS =

CLEANFILES = \
	$(MANPAGE) \
	$(shell find curry -type f -name '*.pyc') \
	$(NULL)

CLEANDIRS = \
	*.egg-info \
	dist \
	build \
	arch/src \
	arch/pkg \
	arch/*.tar* \
	$(NULL)

all: help

help:
	@echo -e "Available targets:\n"
	@echo "  install install $(PROGRAM) on the system"
	@echo "  dist    make a tarball for distribution"
	@echo "  clean   cleanup generated files"

$(MANPAGE): $(MANPAGE).txt
	a2x -fmanpage $<

install: $(MANPAGE)
	$(PYTHON) setup.py install $(INSTALL_ARGS)

dist: $(MANPAGE)
	$(PYTHON) setup.py sdist

clean:
	rm -f $(CLEANFILES)
	rm -rf $(CLEANDIRS)

.PHONY: all help install dist clean
