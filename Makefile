#!/usr/bin/env make -f

PYPY_DIR ?= pypy
RPYTHON  ?= $(PYPY_DIR)/rpython/bin/rpython

.PHONY: compile som-interp som-jit som-ast-jit som-bc-jit som-bc-interp som-ast-interp

all: compile

compile: som-ast-jit

som-ast-jit: core-lib/.git
	SOM_INTERP=AST PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch -Ojit src/main-rpython.py

som-bc-jit:	core-lib/.git
	SOM_INTERP=BC  PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch -Ojit src/main-rpython.py

som-ast-interp: core-lib/.git
	SOM_INTERP=AST PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch src/main-rpython.py

som-bc-interp: core-lib/.git
	SOM_INTERP=BC  PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch src/main-rpython.py

som-interp: som-ast-interp som-bc-interp
	
som-jit: som-ast-jit som-bc-jit

test: compile
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) nosetests
	if [ -e ./som-ast-jit    ]; then ./som-ast-jit    -cp Smalltalk TestSuite/TestHarness.som; fi
	if [ -e ./som-bc-jit     ]; then ./som-bc-jit     -cp Smalltalk TestSuite/TestHarness.som; fi
	if [ -e ./som-ast-interp ]; then ./som-ast-interp -cp Smalltalk TestSuite/TestHarness.som; fi
	if [ -e ./som-bc-interp  ]; then ./som-bc-interp  -cp Smalltalk TestSuite/TestHarness.som; fi

clean:
	@-rm som-ast-jit som-ast-interp
	@-rm som-bc-jit  som-bc-interp

core-lib/.git:
	git submodule update --init
