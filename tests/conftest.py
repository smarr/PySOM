# pylint: disable=redefined-outer-name

from os.path import dirname, realpath

import pytest
from rlib.string_stream import StringStream

from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.vm.current import current_universe
from som.vm.symbols import symbol_for

if is_ast_interpreter():
    from som.compiler.ast.method_generation_context import MethodGenerationContext
    from som.compiler.ast.parser import Parser
    from som.compiler.ast.disassembler import dump_method
else:
    from som.compiler.bc.method_generation_context import MethodGenerationContext
    from som.compiler.bc.parser import Parser
    from som.compiler.bc.disassembler import dump_method


def initialize_universe_for_testing():
    smalltalk_folder = realpath(dirname(__file__) + "/../core-lib/Smalltalk/")
    current_universe.initialize_for_testing(smalltalk_folder)


@pytest.fixture
def cgenc():
    gen_c = ClassGenerationContext(current_universe)
    gen_c.name = symbol_for("Test")
    return gen_c


@pytest.fixture
def mgenc(cgenc):
    mgenc = MethodGenerationContext(current_universe, cgenc, None)
    mgenc.add_argument("self", None, None)
    mgenc.signature = symbol_for("test")
    return mgenc


@pytest.fixture
def bgenc(cgenc, mgenc):
    bgenc = MethodGenerationContext(current_universe, cgenc, mgenc)
    return bgenc


def add_field(cgenc, name):
    cgenc.add_instance_field(symbol_for(name))


def dump(mgenc):
    dump_method(mgenc, b"")


def parse_method(mgenc, source):
    parser = Parser(StringStream(source.strip()), "test", current_universe)
    return parser.method(mgenc)


def parse_block(bgenc, source):
    parser = Parser(StringStream(source.strip()), "test", current_universe)
    return parser.nested_block(bgenc)
