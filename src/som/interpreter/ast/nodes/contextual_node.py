from .expression_node import ExpressionNode

from rlib.jit import unroll_safe


class ContextualNode(ExpressionNode):

    _immutable_fields_ = ["_context_level"]

    def __init__(self, context_level, source_section = None):
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

        block = frame.get_self()
        for i in range(0, self._context_level - 1):
            block = block.get_outer_self()
        return block

    @unroll_safe
    def determine_outer_self(self, frame):
        outer_self = frame.get_self()
        for i in range(0, self._context_level):
            outer_self = outer_self.get_outer_self()
        return outer_self
