# pylint: disable=redefined-outer-name
from collections import deque
import pytest
from rlib.string_stream import StringStream

from som.compiler.bc.disassembler import dump_method
from som.compiler.bc.method_generation_context import MethodGenerationContext
from som.compiler.bc.parser import Parser
from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.interpreter.bc.bytecodes import Bytecodes, bytecode_length, bytecode_as_str
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


@pytest.mark.parametrize(
    "operator,bytecode",
    [
        ("+", Bytecodes.inc),
        ("-", Bytecodes.dec),
    ],
)
def test_inc_dec_bytecodes(mgenc, operator, bytecode):
    bytecodes = method_to_bytecodes(mgenc, "test = ( 1 OP 1 )".replace("OP", operator))

    assert len(bytecodes) == 3
    check(bytecodes, [Bytecodes.push_1, bytecode, Bytecodes.return_self])


def test_empty_method_returns_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( )")

    assert len(bytecodes) == 1
    check(bytecodes, [Bytecodes.return_self])


def test_explicit_return_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ self )")

    assert len(bytecodes) == 1
    check(bytecodes, [Bytecodes.return_self])


def test_dup_pop_argument_pop(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test: arg = ( arg := 1. ^ self )")

    assert len(bytecodes) == 5
    check(bytecodes, [Bytecodes.push_1, Bytecodes.pop_argument, Bytecodes.return_self])


def test_dup_pop_argument_pop_implicit_return_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test: arg = ( arg := 1 )")

    assert len(bytecodes) == 5
    check(bytecodes, [Bytecodes.push_1, Bytecodes.pop_argument, Bytecodes.return_self])


def test_dup_pop_local_pop(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( | local | local := 1. ^ self )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_local == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_field_0_pop(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( field := 1. ^ self )")

    assert len(bytecodes) == 3
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_field_0 == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[2]


def test_dup_pop_field_pop(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( field := 1. ^ self )")

    assert len(bytecodes) == 5
    check(bytecodes, [Bytecodes.push_1, Bytecodes.pop_field, Bytecodes.return_self])


def test_dup_pop_field_return_self(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test: val = ( field := val )")

    assert len(bytecodes) == 5
    check(
        bytecodes,
        [Bytecodes.push_argument, Bytecodes.pop_field_0, Bytecodes.return_self],
    )


def test_dup_pop_field_n_return_self(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test: value = ( field := value )")

    assert len(bytecodes) == 7
    check(
        bytecodes, [Bytecodes.push_argument, Bytecodes.pop_field, Bytecodes.return_self]
    )


def test_send_dup_pop_field_return_local(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ field := self method )")

    assert len(bytecodes) == 8
    check(
        bytecodes,
        [
            Bytecodes.push_argument,
            Bytecodes.send_1,
            Bytecodes.dup,
            Bytecodes.pop_field_0,
            Bytecodes.return_local,
        ],
    )


def test_send_dup_pop_field_return_local_period(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ field := self method. )")

    assert len(bytecodes) == 8
    check(
        bytecodes,
        [
            Bytecodes.push_argument,
            Bytecodes.send_1,
            Bytecodes.dup,
            Bytecodes.pop_field_0,
            Bytecodes.return_local,
        ],
    )


def test_block_dup_pop_argument_pop_return_arg(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1. arg ]")

    assert len(bytecodes) == 8
    check(
        bytecodes,
        [
            Bytecodes.push_1,
            Bytecodes.pop_argument,
            (4, Bytecodes.push_argument),
            Bytecodes.return_local,
        ],
    )


def test_block_dup_pop_argument_pop_implicit_return(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1 ]")

    assert len(bytecodes) == 6
    check(
        bytecodes,
        [
            Bytecodes.push_1,
            Bytecodes.dup,
            Bytecodes.pop_argument,
            Bytecodes.return_local,
        ],
    )


def test_block_dup_pop_argument_pop_implicit_return_dot(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1. ]")

    assert len(bytecodes) == 6
    check(
        bytecodes,
        [
            Bytecodes.push_1,
            Bytecodes.dup,
            Bytecodes.pop_argument,
            Bytecodes.return_local,
        ],
    )


def test_block_dup_pop_local_return_local(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[| local | local := 1 ]")

    assert len(bytecodes) == 6
    check(
        bytecodes,
        [Bytecodes.push_1, Bytecodes.dup, Bytecodes.pop_local, Bytecodes.return_local],
    )


def test_block_dup_pop_field_return_local(cgenc, bgenc):
    add_field(cgenc, "field")
    bytecodes = block_to_bytecodes(bgenc, "[ field := 1 ]")

    assert len(bytecodes) == 6
    check(
        bytecodes,
        [Bytecodes.push_1, Bytecodes.dup, Bytecodes.pop_field, Bytecodes.return_local],
    )


def test_block_dup_pop_field_return_local_dot(cgenc, bgenc):
    add_field(cgenc, "field")
    bytecodes = block_to_bytecodes(bgenc, "[ field := 1. ]")

    assert len(bytecodes) == 6
    check(
        bytecodes,
        [Bytecodes.push_1, Bytecodes.dup, Bytecodes.pop_field, Bytecodes.return_local],
    )


@pytest.mark.parametrize("field_num", range(0, 7))
def test_inc_field(cgenc, mgenc, field_num):
    add_field(cgenc, "field0")
    add_field(cgenc, "field1")
    add_field(cgenc, "field2")
    add_field(cgenc, "field3")
    add_field(cgenc, "field4")
    add_field(cgenc, "field5")
    add_field(cgenc, "field6")

    field_name = "field" + str(field_num)
    bytecodes = method_to_bytecodes(
        mgenc, "test = ( " + field_name + " := " + field_name + " + 1 )"
    )

    check(
        bytecodes,
        [
            BC(Bytecodes.inc_field, field_num, 0),
            Bytecodes.return_self,
        ],
    )


@pytest.mark.parametrize("field_num", range(0, 7))
def test_inc_field_non_trivial(cgenc, mgenc, field_num):
    add_field(cgenc, "field0")
    add_field(cgenc, "field1")
    add_field(cgenc, "field2")
    add_field(cgenc, "field3")
    add_field(cgenc, "field4")
    add_field(cgenc, "field5")
    add_field(cgenc, "field6")

    field_name = "field" + str(field_num)
    bytecodes = method_to_bytecodes(
        mgenc, "test = ( 1. " + field_name + " := " + field_name + " + 1. 2 )"
    )
    check(
        bytecodes,
        [
            Bytecodes.push_1,
            Bytecodes.pop,
            BC(Bytecodes.inc_field, field_num, 0),
            Bytecodes.push_constant_1,
            Bytecodes.return_self,
        ],
    )


@pytest.mark.parametrize("field_num", range(0, 7))
def test_return_inc_field(cgenc, mgenc, field_num):
    add_field(cgenc, "field0")
    add_field(cgenc, "field1")
    add_field(cgenc, "field2")
    add_field(cgenc, "field3")
    add_field(cgenc, "field4")
    add_field(cgenc, "field5")
    add_field(cgenc, "field6")

    field_name = "field" + str(field_num)
    bytecodes = method_to_bytecodes(
        mgenc, "test = ( #foo. ^ " + field_name + " := " + field_name + " + 1 )"
    )
    check(
        bytecodes,
        [
            Bytecodes.push_constant_0,
            Bytecodes.pop,
            BC(Bytecodes.inc_field_push, field_num, 0),
            Bytecodes.return_local,
        ],
    )


@pytest.mark.parametrize("field_num", range(0, 7))
def test_return_inc_field_from_block(cgenc, bgenc, field_num):
    add_field(cgenc, "field0")
    add_field(cgenc, "field1")
    add_field(cgenc, "field2")
    add_field(cgenc, "field3")
    add_field(cgenc, "field4")
    add_field(cgenc, "field5")
    add_field(cgenc, "field6")

    field_name = "field" + str(field_num)
    bytecodes = block_to_bytecodes(
        bgenc, "[ #foo. " + field_name + " := " + field_name + " + 1 ]"
    )

    check(
        bytecodes,
        [
            Bytecodes.push_constant_0,
            Bytecodes.pop,
            BC(Bytecodes.inc_field_push, field_num, 1),
            Bytecodes.return_local,
        ],
    )


@pytest.mark.parametrize(
    "field_num,bytecode",
    [
        (0, Bytecodes.return_field_0),
        (1, Bytecodes.return_field_1),
        (2, Bytecodes.return_field_2),
        (3, BC(Bytecodes.push_field, 3)),
        (4, BC(Bytecodes.push_field, 4)),
    ],
)
def test_return_field(cgenc, mgenc, field_num, bytecode):
    add_field(cgenc, "field0")
    add_field(cgenc, "field1")
    add_field(cgenc, "field2")
    add_field(cgenc, "field3")
    add_field(cgenc, "field4")
    add_field(cgenc, "field5")
    add_field(cgenc, "field6")

    field_name = "field" + str(field_num)
    bytecodes = method_to_bytecodes(mgenc, "test = ( 1. ^ " + field_name + " )")

    check(
        bytecodes,
        [
            Bytecodes.push_1,
            Bytecodes.pop,
            bytecode,
        ],
    )
