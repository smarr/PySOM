import pytest
from tests.conftest import parse_method, add_field
from som.interpreter.ast.nodes.block_node import BlockNode
from som.interp_type import is_bytecode_interpreter
from som.interpreter.ast.nodes.supernodes.field_string_equal_node import (
    LocalFieldStringEqualsNode,
    NonLocalFieldStringEqualsNode,
)
from som.interpreter.ast.nodes.supernodes.string_equals_node import StringEqualsNode


pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    is_bytecode_interpreter(), reason="Tests are specific to AST interpreter"
)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("field = 'str'", LocalFieldStringEqualsNode),
        ("arg = 'str'", StringEqualsNode),
        ("var = 'str'", StringEqualsNode),
        ("('s' + 'dd') = 'str'", StringEqualsNode),
        ("'str' = field", LocalFieldStringEqualsNode),
        ("'str' = arg", StringEqualsNode),
        ("'str' = var", StringEqualsNode),
        ("'str' = ('s' + 'dd')", StringEqualsNode),
    ],
)
def test_method_optimization(cgenc, mgenc, source, expected_node):
    add_field(cgenc, "field")
    body = parse_method(mgenc, "test: arg = ( | var | \n ^ " + source + " )")
    assert isinstance(body, expected_node)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("[ field = 'str' ] ", NonLocalFieldStringEqualsNode),
        ("[ arg = 'str' ]", StringEqualsNode),
        ("[ var = 'str' ]", StringEqualsNode),
        ("[:a | a = 'str' ]", StringEqualsNode),
        ("[ | v | v = 'str' ]", StringEqualsNode),
        ("[ ('s' + 'dd') = 'str' ]", StringEqualsNode),
        ("[ 'str' = field ]", NonLocalFieldStringEqualsNode),
        ("[ 'str' = arg ]", StringEqualsNode),
        ("[ 'str' = var ]", StringEqualsNode),
        ("[:a | 'str' = a ]", StringEqualsNode),
        ("[ | v |  'str' = v ]", StringEqualsNode),
        ("[ 'str' = ('s' + 'dd') ]", StringEqualsNode),
    ],
)
def test_block_optimization(cgenc, mgenc, source, expected_node):
    add_field(cgenc, "field")
    body = parse_method(mgenc, "test: arg = ( | var | \n ^ " + source + " )")
    assert isinstance(body, BlockNode)

    block_body = body.get_method().invokable.expr_or_sequence
    assert isinstance(block_body, expected_node)
