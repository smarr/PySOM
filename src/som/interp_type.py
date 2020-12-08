import os
import sys

from rlib import jit

_interp_type_str = os.getenv('SOM_INTERP', None)

_AST = 1
_BC = 2
_UNKNOWN = 3


def _get_interp_type():
    if _interp_type_str is None or not (_interp_type_str in ['AST', 'BC']):
        print("Type of interpreter not set. Please set the SOM_INTERP environment variable")
        print("\tSOM_INTERP=AST   Use an Abstract Syntax Tree interpreter")
        print("\tSOM_INTERP=BC    Use a Bytecode interpreter")
        sys.exit(1)
    if _interp_type_str == 'AST':
        return _AST
    if _interp_type_str == 'BC':
        return _BC
    return _UNKNOWN


_interp_type = _get_interp_type()


def get_interpreter_type():
    return _interp_type


@jit.elidable
def is_bytecode_interpreter():
    return _interp_type == _BC


@jit.elidable
def is_ast_interpreter():
    return _interp_type == _AST
