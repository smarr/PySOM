#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from som.compiler.parse_error import ParseError
from som.interp_type import is_ast_interpreter, is_bytecode_interpreter
from som.vm.universe import main, Exit

import os

try:
    import rpython.rlib
except ImportError:
    "NOT_RPYTHON"
    print("Failed to load RPython library. Please make sure it is on PYTHONPATH")
    sys.exit(1)

# __________  Entry points  __________


def entry_point(argv):
    try:
        main(argv)
    except Exit as e:
        return e.code
    except ParseError as e:
        os.write(2, str(e))
        return 1
    except Exception as e:
        os.write(2, "ERROR: %s thrown during execution.\n" % e)
        return 1
    return 1


# _____ Define and setup target ___


def target(driver, args):
    exe_name = 'som-'
    if is_ast_interpreter():
        exe_name += 'ast-'
    elif is_bytecode_interpreter():
        exe_name += 'bc-'

    if driver.config.translation.jit:
        exe_name += 'jit'
    else:
        exe_name += 'interp'

    driver.exe_name = exe_name
    return entry_point, None


def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()


if __name__ == '__main__':
    from rpython.translator.driver import TranslationDriver
    f, _ = target(TranslationDriver(), sys.argv)
    sys.exit(f(sys.argv))
