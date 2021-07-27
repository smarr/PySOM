# pylint: disable=redefined-outer-name
import pytest
from rlib.string_stream import StringStream

from som.compiler.bc.disassembler import dump_method
from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.vm.current import current_universe
from som.vmobjects.method_ast import AstMethod
from som.vmobjects.method_bc import BcMethod
from som.vmobjects.method_trivial import (
    LiteralReturn,
    GlobalRead,
    FieldRead,
    FieldWrite,
)

if is_ast_interpreter():
    from som.compiler.ast.method_generation_context import MethodGenerationContext
    from som.compiler.ast.parser import Parser
else:
    from som.compiler.bc.method_generation_context import MethodGenerationContext
    from som.compiler.bc.parser import Parser


def add_field(cgenc, name):
    cgenc.add_instance_field(current_universe.symbol_for(name))


def dump(mgenc):
    dump_method(mgenc, "")


@pytest.fixture
def cgenc():
    gen_c = ClassGenerationContext(current_universe)
    gen_c.name = current_universe.symbol_for("Test")
    return gen_c


@pytest.fixture
def mgenc(cgenc):
    mgenc = MethodGenerationContext(current_universe, cgenc, None)
    mgenc.add_argument("self")
    mgenc.signature = current_universe.symbol_for("test")
    return mgenc


@pytest.fixture
def bgenc(cgenc, mgenc):
    bgenc = MethodGenerationContext(current_universe, cgenc, mgenc)
    bgenc.add_argument("$blockSelf")
    return bgenc


def parse_method(mgenc, source):
    parser = Parser(StringStream(source), "test", current_universe)
    return parser.method(mgenc)


def parse_block(bgenc, source):
    parser = Parser(StringStream(source), "test", current_universe)
    return parser.nested_block(bgenc)


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
    body_or_none = parse_method(mgenc, "test = ( ^ " + source + " )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, LiteralReturn)
    assert str(m.invoke_1(None)) == test_result


@pytest.mark.parametrize("source", ["Nil", "system", "MyClassFooBar"])
def test_global_return(mgenc, source):
    body_or_none = parse_method(mgenc, "test = ( ^ " + source + " )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, GlobalRead)


def test_field_getter_0(cgenc, mgenc):
    add_field(cgenc, "field")
    body_or_none = parse_method(mgenc, "test = ( ^ field )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, FieldRead)


def test_field_getter_n(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    body_or_none = parse_method(mgenc, "test = ( ^ field )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, FieldRead)


@pytest.mark.parametrize(
    "source", ["field := val", "field := val.", "field := val. ^ self"]
)
def test_field_setter_0(cgenc, mgenc, source):
    add_field(cgenc, "field")
    body_or_none = parse_method(mgenc, "test: val = ( " + source + " )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, FieldWrite)


@pytest.mark.parametrize(
    "source", ["field := value", "field := value.", "field := value. ^ self"]
)
def test_field_setter_n(cgenc, mgenc, source):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    body_or_none = parse_method(mgenc, "test: value = ( " + source + " )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, FieldWrite)


@pytest.mark.parametrize(
    "source",
    [
        "0",
        "1",
        "-10",
        "'str'",
        "#sym",
        "1.1",
        "-2342.234",
        "true",
        "false",
        "nil",
    ],
)
def test_literal_no_return(mgenc, source):
    body_or_none = parse_method(mgenc, "test = ( " + source + " )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, AstMethod) or isinstance(m, BcMethod)


def test_block_return(mgenc):
    body_or_none = parse_method(mgenc, "test = ( ^ [] )")
    m = mgenc.assemble(body_or_none)
    assert isinstance(m, AstMethod) or isinstance(m, BcMethod)


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
    body_or_none = parse_block(bgenc, "[ " + source + " ]")
    m = bgenc.assemble(body_or_none)
    assert isinstance(m, LiteralReturn)
    assert str(m.invoke_1(None)) == test_result
