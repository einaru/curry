### Makefile for curry

PYTHON = python3
SETUP_PY_FLAGS = --optimize=1
MAN_PAGE = data/curry.1

CLEANFILES = *.egg-info dist \
			 `find curry -type d -name '__pycache__'` \
			 arch/src \
			 arch/pkg \
			 arch/*.tar* \

.PHONY: install dist manpage clean

install:
	$(PYTHON) setup.py install $(SETUP_PY_FLAGS)

dist:
	$(PYTHON) setup.py sdist

manpage:
	a2x -fmanpage $(MAN_PAGE).txt
	gzip -f $(MAN_PAGE)

clean:
	rm -rf $(CLEANFILES)
