# pylint: disable=redefined-outer-name
from collections import deque
import pytest
from rlib.string_stream import StringStream

from som.compiler.bc.disassembler import dump_method
from som.compiler.bc.method_generation_context import MethodGenerationContext
from som.compiler.bc.parser import Parser
from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.interpreter.bc.bytecodes import bytecode_length, bytecode_as_str
from som.vm.current import current_universe
from som.vm.symbols import symbol_for

pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    is_ast_interpreter(), reason="Tests are specific to bytecode interpreter"
)


def add_field(cgenc, name):
    cgenc.add_instance_field(symbol_for(name))


def dump(mgenc):
    dump_method(mgenc, "")


@pytest.fixture
def cgenc():
    gen_c = ClassGenerationContext(current_universe)
    gen_c.name = symbol_for("Test")
    return gen_c


@pytest.fixture
def mgenc(cgenc):
    mgenc = MethodGenerationContext(current_universe, cgenc, None)
    mgenc.add_argument("self", None, None)
    return mgenc


@pytest.fixture
def bgenc(cgenc, mgenc):
    mgenc.signature = symbol_for("test")
    bgenc = MethodGenerationContext(current_universe, cgenc, mgenc)
    return bgenc


def method_to_bytecodes(mgenc, source, dump_bytecodes=False):
    parser = Parser(StringStream(source.strip()), "test", current_universe)
    parser.method(mgenc)
    if dump_bytecodes:
        dump(mgenc)
    return mgenc.get_bytecodes()


def block_to_bytecodes(bgenc, source):
    parser = Parser(StringStream(source), "test", current_universe)

    parser.nested_block(bgenc)
    return bgenc.get_bytecodes()


class BC(object):
    def __init__(self, bytecode, arg1=None, arg2=None, note=None):
        self.bytecode = bytecode
        self.arg1 = arg1
        self.arg2 = arg2
        self.note = note


def check(actual, expected):
    expected_q = deque(expected)
    i = 0
    while i < len(actual) and expected_q:
        actual_bc = actual[i]
        bc_length = bytecode_length(actual_bc)

        expected_bc = expected_q[0]
        if isinstance(expected_bc, tuple):
            if expected_bc[0] == i:
                expected_bc = expected_bc[1]
            else:
                assert expected_bc[0] > i
                i += bc_length
                continue

        if isinstance(expected_bc, BC):
            assert actual_bc == expected_bc.bytecode, (
                "Bytecode "
                + str(i)
                + " expected "
                + bytecode_as_str(expected_bc.bytecode)
                + " but got "
                + bytecode_as_str(actual_bc)
            )
            if expected_bc.arg1 is not None:
                assert actual[i + 1] == expected_bc.arg1, (
                    "Bytecode "
                    + str(i)
                    + " expected "
                    + bytecode_as_str(expected_bc.bytecode)
                    + "("
                    + str(expected_bc.arg1)
                    + ", "
                    + str(expected_bc.arg2)
                    + ") but got "
                    + bytecode_as_str(actual_bc)
                    + "("
                    + str(actual[i + 1])
                    + ", "
                    + str(actual[i + 2])
                    + ")"
                )
            if expected_bc.arg2 is not None:
                assert actual[i + 2] == expected_bc.arg2
        else:
            assert actual_bc == expected_bc, (
                "Bytecode "
                + str(i)
                + " expected "
                + bytecode_as_str(expected_bc)
                + " but got "
                + bytecode_as_str(actual_bc)
            )
        expected_q.popleft()

        i += bc_length

    assert len(expected_q) == 0
