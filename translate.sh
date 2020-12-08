#!/bin/sh

# to translate interpreter: ./translate.sh interp
# to translate jit        : ./translate.sh
if [ -z "$1" ]
then
  OPT="-Ojit"
fi

../pypy/rpython/bin/rpython $OPT src/main-rpython.py
