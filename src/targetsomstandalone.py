#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from som.vm.universe import main, Exit
from rpython.rlib import jit
#from rpython.rlib.debug import debug_start, debug_stop, debug_print


# __________  Entry points  __________

def entry_point(argv):
    try:
        main(argv)
    except Exit, e:
        return e.code
    return 1


# _____ Define and setup target ___


def target(driver, args):
    driver.exe_name = 'som'
    return entry_point, None


def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()


if __name__ == '__main__':
    from rpython.translator.driver import TranslationDriver
    f, _ = target(TranslationDriver(), sys.argv)
    sys.exit(f(sys.argv))
