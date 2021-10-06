#!/usr/bin/env make -f

PYPY_DIR ?= pypy
RPYTHON  ?= $(PYPY_DIR)/rpython/bin/rpython

.PHONY: compile som-interp som-jit som-ast-jit som-ast-interp

all: compile

compile: som-ast-jit

som-ast-jit: core-lib/.git
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch -Ojit src/main_rpython.py

som-ast-interp: core-lib/.git
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch src/main_rpython.py
	
test: compile
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) nosetests
	if [ -e ./som-ast-jit    ]; then ./som-ast-jit    -cp Smalltalk TestSuite/TestHarness.som; fi
	if [ -e ./som-ast-interp ]; then ./som-ast-interp -cp Smalltalk TestSuite/TestHarness.som; fi

clean:
	@-rm som-ast-jit som-ast-interp

core-lib/.git:
	git submodule update --init
