# pylint: disable=redefined-outer-name
import pytest
from rlib.string_stream import StringStream

from som.compiler.bc.disassembler import dump_method
from som.compiler.bc.method_generation_context import MethodGenerationContext
from som.compiler.bc.parser import Parser
from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.interpreter.bc.bytecodes import Bytecodes
from som.vm.current import current_universe
from som.vmobjects.method_trivial import (
    LiteralReturn,
    GlobalRead,
    FieldRead,
    FieldWrite,
)

pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    is_ast_interpreter(), reason="Tests are specific to bytecode interpreter"
)


def add_field(cgenc, name):
    cgenc.add_instance_field(current_universe.symbol_for(name))


def dump(mgenc):
    dump_method(mgenc, "")


@pytest.fixture
def cgenc():
    return ClassGenerationContext(current_universe)


@pytest.fixture
def mgenc(cgenc):
    mgenc = MethodGenerationContext(current_universe, cgenc, None)
    mgenc.add_argument("self")
    return mgenc


@pytest.fixture
def bgenc(cgenc, mgenc):
    bgenc = MethodGenerationContext(current_universe, cgenc, mgenc)
    bgenc.add_argument("$blockSelf")
    return bgenc


def method_to_bytecodes(mgenc, source):
    parser = Parser(StringStream(source), "test", current_universe)
    parser.method(mgenc)
    return mgenc.get_bytecodes()


def block_to_bytecodes(bgenc, source):
    parser = Parser(StringStream(source), "test", current_universe)

    parser.nested_block(bgenc)
    return bgenc.get_bytecodes()


def test_empty_method_returns_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( )")

    assert len(bytecodes) == 1
    assert bytecodes[0] == Bytecodes.return_self


def test_explicit_return_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ self )")

    assert len(bytecodes) == 1
    assert bytecodes[0] == Bytecodes.return_self


def test_dup_pop_argument_pop(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test: arg = ( arg := 1. ^ self )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_argument == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_argument_pop_implicit_return_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test: arg = ( arg := 1 )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_argument == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


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
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_field == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_field_return_self(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test: val = ( field := val )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.pop_field_0 == bytecodes[3]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_field_n_return_self(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test: value = ( field := value )")

    assert len(bytecodes) == 7
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.pop_field == bytecodes[3]
    assert Bytecodes.return_self == bytecodes[6]


def test_send_dup_pop_field_return_local(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ field := self method )")

    assert len(bytecodes) == 8
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.send_1 == bytecodes[3]
    assert Bytecodes.dup == bytecodes[5]
    assert Bytecodes.pop_field_0 == bytecodes[6]
    assert Bytecodes.return_local == bytecodes[7]


def test_send_dup_pop_field_return_local_period(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ field := self method. )")

    assert len(bytecodes) == 8
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.send_1 == bytecodes[3]
    assert Bytecodes.dup == bytecodes[5]
    assert Bytecodes.pop_field_0 == bytecodes[6]
    assert Bytecodes.return_local == bytecodes[7]


@pytest.mark.parametrize(
    "source,test_result",
    [
        ("0", "0"),
        ("1", "1"),
        ("-10", "-10"),
        ("3333", "3333"),
        ("'str'", '"str"'),
        ("#sym", "#sym"),
        ("1.1", "1.1"),
        ("-2342.234", "-2342.234"),
        ("true", "true"),
        ("false", "false"),
        ("nil", "nil"),
    ],
)
def test_literal_return(mgenc, source, test_result):
    method_to_bytecodes(mgenc, "test = ( ^ " + source + " )")
    m = mgenc.assemble(None)
    assert isinstance(m, LiteralReturn)
    assert str(m.invoke_1(None)) == test_result


@pytest.mark.parametrize("source", ["Nil", "system", "MyClassFooBar"])
def test_global_return(mgenc, source):
    method_to_bytecodes(mgenc, "test = ( ^ " + source + " )")
    m = mgenc.assemble(None)
    assert isinstance(m, GlobalRead)


def test_field_getter_0(cgenc, mgenc):
    add_field(cgenc, "field")
    method_to_bytecodes(mgenc, "test = ( ^ field )")
    m = mgenc.assemble(None)
    assert isinstance(m, FieldRead)


def test_field_getter_n(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    method_to_bytecodes(mgenc, "test = ( ^ field )")
    m = mgenc.assemble(None)
    assert isinstance(m, FieldRead)


def test_field_setter_0(cgenc, mgenc):
    add_field(cgenc, "field")
    method_to_bytecodes(mgenc, "test: val = ( field := val )")
    m = mgenc.assemble(None)
    assert isinstance(m, FieldWrite)


def test_field_setter_n(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    method_to_bytecodes(mgenc, "test: value = ( field := value )")
    m = mgenc.assemble(None)
    assert isinstance(m, FieldWrite)


def test_block_dup_pop_argument_pop(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1. arg ]")

    assert len(bytecodes) == 8
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_argument == bytecodes[1]
    assert Bytecodes.push_argument == bytecodes[4]
    assert Bytecodes.return_local == bytecodes[7]


def test_block_dup_pop_argument_pop_implicit_return_self(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1 ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_argument == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_argument_pop_implicit_return_self_dot(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1. ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_argument == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_local_return_local(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[| local | local := 1 ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_local == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_field_return_local(cgenc, bgenc):
    add_field(cgenc, "field")
    bytecodes = block_to_bytecodes(bgenc, "[ field := 1 ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_field == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_field_return_local_dot(cgenc, bgenc):
    add_field(cgenc, "field")
    bytecodes = block_to_bytecodes(bgenc, "[ field := 1. ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_field == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


@pytest.mark.parametrize(
    "source,test_result",
    [
        ("0", "0"),
        ("1", "1"),
        ("-10", "-10"),
        ("3333", "3333"),
        ("'str'", '"str"'),
        ("#sym", "#sym"),
        ("1.1", "1.1"),
        ("-2342.234", "-2342.234"),
        ("true", "true"),
        ("false", "false"),
        ("nil", "nil"),
    ],
)
def test_block_literal_return(bgenc, source, test_result):
    block_to_bytecodes(bgenc, "[ " + source + " ]")
    m = bgenc.assemble(None)
    assert isinstance(m, LiteralReturn)
    assert str(m.invoke_1(None)) == test_result
