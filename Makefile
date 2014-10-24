### Makefile for curry

PYTHON = python3
SETUP_PY_FLAGS = --optimize=1
CLEANFILES = *.egg-info dist \
			 `find curry -type d -name '__pycache__'` \

.PHONY: install dist clean

install:
	$(PYTHON) setup.py install $(SETUP_PY_FLAGS)

dist:
	$(PYTHON) setup.py sdist

clean:
	rm -rf $(CLEANFILES)
