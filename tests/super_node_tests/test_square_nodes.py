import pytest
from tests.conftest import parse_method, initialize_universe_for_testing

from som.interp_type import is_bytecode_interpreter
from som.interpreter.ast.frame import create_frame_1, write_frame
from som.interpreter.ast.nodes.return_non_local_node import ReturnNonLocalNode
from som.interpreter.ast.nodes.variable_node import UninitializedWriteNode
from som.interpreter.ast.nodes.block_node import BlockNode
from som.interpreter.ast.nodes.message.uninitialized_node import (
    UninitializedMessageNode,
)
from som.interpreter.ast.nodes.supernodes.square_node import (
    UninitializedVarSquareNode,
    LocalFrameReadSquareWriteNode,
    NonLocalReadSquareWriteNode,
)
from som.vmobjects.integer import Integer

pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    is_bytecode_interpreter(), reason="Tests are specific to AST interpreter"
)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("l2 * l2.", UninitializedVarSquareNode),
        ("l1 * l1.", UninitializedVarSquareNode),
        ("l1 * l3.", UninitializedMessageNode),
        ("l1 := l2 * l2", UninitializedWriteNode),
        ("l2 := l2 * l2", UninitializedWriteNode),
        ("l3 := l1 * l2", UninitializedWriteNode),
    ],
)
def test_method_optimization(mgenc, source, expected_node):
    body = parse_method(mgenc, "test = ( | l1 l2 l3 l4 |  ^ " + source + " )")
    assert isinstance(body, expected_node)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("l1 := l2 * l2", LocalFrameReadSquareWriteNode),
        ("l2 := l2 * l2", LocalFrameReadSquareWriteNode),
    ],
)
def test_method_self_opt(mgenc, source, expected_node):
    body = parse_method(mgenc, "test = ( | l1 l2 l3 l4 |  ^ " + source + " )")
    method = mgenc.assemble(body)
    frame = create_frame_1(None, 5, 0)

    for i in range(4):
        write_frame(frame, i, Integer(1))

    assert isinstance(body, UninitializedWriteNode)
    assert body is method.invokable.expr_or_sequence
    body.execute(frame)

    assert body is not method.invokable.expr_or_sequence
    assert isinstance(method.invokable.expr_or_sequence, expected_node)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("[ l2 * l2 ]", UninitializedVarSquareNode),
        ("[ l1 * l1 ]", UninitializedVarSquareNode),
        ("[:a | a * a ]", UninitializedVarSquareNode),
        ("[ | bl | bl * bl ]", UninitializedVarSquareNode),
        ("[ l1 * l1 ]", UninitializedVarSquareNode),
        ("[ l1 * l3 ]", UninitializedMessageNode),
        ("[ l3 := l1 * l2 ]", UninitializedWriteNode),
    ],
)
def test_block_optimization(mgenc, source, expected_node):
    body = parse_method(mgenc, "test = ( | l1 l2 l3 l4 |  ^ " + source + " )")
    assert isinstance(body, BlockNode)
    block_body = body.get_method().invokable.expr_or_sequence
    assert isinstance(block_body, expected_node)


@pytest.mark.parametrize(
    "source,expected_node",
    [
        ("[ ^ l1 := l2 * l2 ]", NonLocalReadSquareWriteNode),
        ("[ ^ l2 := l2 * l2 ]", NonLocalReadSquareWriteNode),
    ],
)
def test_block_self_opt(mgenc, source, expected_node):
    initialize_universe_for_testing()

    body = parse_method(
        mgenc,
        "test = ( | l1 l2 l3 l4 |"
        "  l1 := l3 := l4 := 1."
        "  l2 := 2."
        "  ^ " + source + " value )",
    )
    method = mgenc.assemble(body)

    result = method.invoke_1(None)
    assert result.get_embedded_integer() == 4

    block_method = method._embedded_block_methods[0]  # pylint: disable=protected-access
    should_be_non_local_return = block_method.invokable.expr_or_sequence
    assert isinstance(should_be_non_local_return, ReturnNonLocalNode)
    assert isinstance(
        should_be_non_local_return._expr,  # pylint: disable=protected-access
        expected_node,
    )
