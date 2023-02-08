from rlib.jit import unroll_safe
from som.interpreter.ast.frame import FRAME_AND_INNER_RCVR_IDX, read_frame

from som.interpreter.ast.nodes.expression_node import ExpressionNode


class ContextualNode(ExpressionNode):
    _immutable_fields_ = ["_context_level"]

    def __init__(self, context_level, source_section=None):
        ExpressionNode.__init__(self, source_section)
        assert context_level >= 0
        self._context_level = context_level

    def get_context_level(self):
        return self._context_level

    def accesses_outer_context(self):
        return self._context_level > 0

    @unroll_safe
    def determine_block(self, frame):
        assert self._context_level > 0

        block = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
        for _ in range(0, self._context_level - 1):
            block = block.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
        return block

    @unroll_safe
    def determine_outer_self(self, frame):
        outer_self = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
        for _ in range(0, self._context_level):
            outer_self = outer_self.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
        return outer_self
