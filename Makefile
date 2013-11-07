#!/usr/bin/env make -f

all: compile

compile: som.sh

test:
	nosetests
