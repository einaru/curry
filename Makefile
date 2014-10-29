### Makefile for curry

PYTHON = python3
MANPAGE = data/curry.1

CLEANFILES = *.egg-info \
			 dist \
			 `find curry -type d -name '__pycache__'` \
			 arch/src \
			 arch/pkg \
			 arch/*.tar* \

.PHONY: dist manpage clean

dist:
	$(PYTHON) setup.py sdist

manpage:
	a2x -fmanpage -dmanpage $(MANPAGE).txt

clean:
	rm -rf $(CLEANFILES)
