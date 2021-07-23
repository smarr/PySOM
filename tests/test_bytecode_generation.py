import pytest
from rlib.string_stream import StringStream
from unittest import TestCase

from som.compiler.bc.method_generation_context import MethodGenerationContext
from som.compiler.bc.parser import Parser
from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.interpreter.bc.bytecodes import Bytecodes
from som.vm.current import current_universe


@pytest.mark.skipif(is_ast_interpreter(), reason="Tests are specific to bytecode interpreter")
class BytecodeGenerationTest(TestCase):
    def test_empty_method_returns_self(self):
        source = """test = ( )"""
        parser = Parser(StringStream(source), "test", current_universe)

        cgenc = ClassGenerationContext(current_universe)
        mgenc = MethodGenerationContext(current_universe)
        mgenc.holder = cgenc
        mgenc.add_argument("self")

        parser.method(mgenc)

        bytecodes = mgenc.get_bytecodes()

        self.assertEqual(1, len(bytecodes))
        self.assertEqual(Bytecodes.return_self, bytecodes[0])
