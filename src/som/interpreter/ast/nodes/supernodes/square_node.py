from som.interpreter.ast.frame import read_frame, FRAME_AND_INNER_RCVR_IDX, read_inner
from som.interpreter.ast.nodes.variable_node import LocalFrameVarReadNode, NonLocalVariableReadNode, \
    LocalInnerVarReadNode, UninitializedReadNode
from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vmobjects.block_ast import AstBlock


class NonLocalVariableSquareNode(NonLocalVariableReadNode):
    def execute(self, frame):
        block = self.determine_block(frame)
        assert isinstance(block, AstBlock)
        value = block.get_from_outer(self._frame_idx)
        return value.prim_multiply(value)

    def handle_inlining(self, mgenc):
        self._context_level -= 1
        if self._context_level == 0:
            if self._frame_idx == FRAME_AND_INNER_RCVR_IDX:
                # this is the self access
                raise NotImplementedError("not yet implemented")
                # self.replace(
                #     LocalFrameVarReadNode(self._frame_idx, self.source_section)
                # )
            else:
                raise NotImplementedError("not yet implemented")

    def handle_outer_inlined(self, removed_ctx_level, mgenc_with_inlined):
        pass


class LocalFrameVarSquareNode(LocalFrameVarReadNode):
    def execute(self, frame):
        value = read_frame(frame, self._frame_idx)
        return value.prim_multiply(value)


class LocalInnerVarSquareNode(LocalInnerVarReadNode):
    def execute(self, frame):
        value = read_inner(frame, self._frame_idx)
        return value.prim_multiply(value)


class UninitializedVarSquareNode(ExpressionNode):
    _immutable_fields_ = ["_var_read_node"]
    _child_nodes_ = ["_var_read_node"]

    def __init__(self, receiver_expr, source_section):
        ExpressionNode.__init__(self, source_section)
        self._var_read_node = receiver_expr

    def execute(self, frame):
        return self._specialize().execute(frame)

    def _specialize(self):
        node = self._var_read_node
        assert isinstance(node, UninitializedReadNode)
        return self.replace(
            node.var.get_square_node(
                node._context_level, self.source_section))
