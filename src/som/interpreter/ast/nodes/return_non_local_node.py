from som.interpreter.ast.frame import (
    mark_as_no_longer_on_stack,
    FRAME_AND_INNER_RCVR_IDX,
    read_frame,
    get_inner_as_context,
)
from som.interpreter.ast.nodes.contextual_node import ContextualNode
from som.interpreter.ast.nodes.expression_node import ExpressionNode

from som.interpreter.control_flow import ReturnException
from som.interpreter.send import lookup_and_send_2


class ReturnNonLocalNode(ContextualNode):

    _immutable_fields_ = ["_expr?", "universe"]
    _child_nodes_ = ["_expr"]

    def __init__(self, context_level, expr, universe, source_section=None):
        ContextualNode.__init__(self, context_level, source_section)
        self._expr = self.adopt_child(expr)
        self.universe = universe

    def execute(self, frame):
        result = self._expr.execute(frame)
        block = self.determine_block(frame)

        if block.is_outer_on_stack():
            raise ReturnException(result, block.get_on_stack_marker())
        block = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
        outer_self = block.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
        return lookup_and_send_2(outer_self, block, "escapedBlock:")


class CatchNonLocalReturnNode(ExpressionNode):

    _immutable_fields_ = ["_method_body?"]
    _child_nodes_ = ["_method_body"]

    def __init__(self, method_body, source_section=None):
        ExpressionNode.__init__(self, source_section)
        self._method_body = self.adopt_child(method_body)

    def execute(self, frame):
        inner = get_inner_as_context(frame)
        assert isinstance(inner, list)

        try:
            return self._method_body.execute(frame)
        except ReturnException as ex:
            if not ex.has_reached_target(inner):
                raise ex
            return ex.get_result()
        finally:
            mark_as_no_longer_on_stack(inner)
