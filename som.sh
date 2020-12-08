#!/bin/sh
DIR="`dirname \"$0\"`"
if [ -z "$PYTHON" ]; then
  PYTHON=pypy
fi
if [ -z "$PYPY_DIR" ]; then
  PYPY_DIR=$DIR/pypy
fi
export PYTHONPATH=$DIR/src:$PYPY_DIR:$PYTHONPATH
exec $PYTHON $DIR/src/main.py "$@"
