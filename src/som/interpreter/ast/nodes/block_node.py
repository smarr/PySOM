from som.interpreter.ast.frame import get_inner_as_context
from som.vmobjects.block_ast import AstBlock
from som.interpreter.ast.nodes.literal_node import LiteralNode


class BlockNode(LiteralNode):

    _immutable_fields_ = ["universe"]

    def __init__(self, value, universe, source_section=None):
        LiteralNode.__init__(self, value, source_section)
        self.universe = universe

    def execute(self, _frame):
        return AstBlock(self._value, None)


class BlockNodeWithContext(BlockNode):
    def __init__(self, value, universe, source_section=None):
        BlockNode.__init__(self, value, universe, source_section)

    def execute(self, frame):
        return AstBlock(self._value, get_inner_as_context(frame))
