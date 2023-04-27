import pytest
from tests.conftest import parse_method
from som.interp_type import is_bytecode_interpreter
from som.interpreter.ast.nodes.supernodes.compare_int_literal_node import (
    GreaterThanIntNode,
    LessThanIntNode,
    UninitializedLocalLessOrGreaterThanNode,
)

pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    is_bytecode_interpreter(), reason="Tests are specific to AST interpreter"
)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("arg > 0", UninitializedLocalLessOrGreaterThanNode),
        ("(1 + 3) > 0", GreaterThanIntNode),
        ("l1 > 0", UninitializedLocalLessOrGreaterThanNode),
        ("3 > 0", GreaterThanIntNode),
        ("arg < 0", UninitializedLocalLessOrGreaterThanNode),
        ("(1 + 3) < 0", LessThanIntNode),
        ("l1 < 0", UninitializedLocalLessOrGreaterThanNode),
        ("3 < 0", LessThanIntNode),
    ],
)
def test_method_optimization(mgenc, source, expected_node):
    body = parse_method(mgenc, "test: arg = ( | l1 | \n ^ " + source + " )")
    assert isinstance(body, expected_node)
