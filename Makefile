#!/usr/bin/env make -f

all: compile

compile: som.sh

test:
	nosetests
	./som.sh -cp Smalltalk TestSuite/TestHarness.som

clean:
	@echo Delete *.pyc files
	@find . -name "*.pyc" -delete
