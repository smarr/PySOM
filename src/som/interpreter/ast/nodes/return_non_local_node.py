from som.interpreter.ast.frame import (
    mark_as_no_longer_on_stack,
    get_inner_as_context,
    read_frame,
    FRAME_AND_INNER_RCVR_IDX,
    is_on_stack,
)
from som.interpreter.ast.nodes.contextual_node import ContextualNode
from som.interpreter.ast.nodes.expression_node import ExpressionNode

from som.interpreter.control_flow import ReturnException
from som.interpreter.send import lookup_and_send_2


class ReturnLocalNode(ExpressionNode):
    _immutable_fields_ = ["_expr?", "universe"]
    _child_nodes_ = ["_expr"]

    def __init__(self, expr, universe, source_section=None):
        ExpressionNode.__init__(self, source_section)
        self._expr = self.adopt_child(expr)
        self.universe = universe

    def execute(self, frame):
        result = self._expr.execute(frame)
        inner = get_inner_as_context(frame)

        assert is_on_stack(inner)
        raise ReturnException(result, inner)


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
        outer_self = self.determine_outer_self(frame)
        self_block = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
        return lookup_and_send_2(outer_self, self_block, "escapedBlock:")

    def handle_inlining(self, mgenc):
        self._context_level -= 1
        if self._context_level == 0:
            self.replace(
                ReturnLocalNode(self._expr, self.universe, self.source_section)
            )
        assert self._context_level >= 0

    def handle_outer_inlined(self, removed_ctx_level, mgenc_with_inlined):
        self._context_level -= 1
        if self._context_level == 0:
            self.replace(
                ReturnLocalNode(self._expr, self.universe, self.source_section)
            )
        assert self._context_level >= 0


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
