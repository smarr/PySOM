from rlib.jit import unroll_safe
from som.interpreter.ast.frame import (
    read_frame,
    FRAME_AND_INNER_RCVR_IDX,
    read_inner,
    write_frame,
)
from som.interpreter.ast.nodes.variable_node import (
    LocalFrameVarReadNode,
    NonLocalVariableReadNode,
    LocalInnerVarReadNode,
    UninitializedReadNode,
)
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
            raise NotImplementedError("not yet implemented")

    def handle_outer_inlined(self, removed_ctx_level, mgenc_with_inlined):
        assert (
            self._context_level > removed_ctx_level
        ), "TODO: do I need to think about this more?"
        self._context_level -= 1
        assert (
            self._context_level > 0
        ), "This should remain true, because a block enclosing this one got inlined somewhere"


class LocalFrameVarSquareNode(LocalFrameVarReadNode):
    def execute(self, frame):
        value = read_frame(frame, self._frame_idx)
        return value.prim_multiply(value)


class LocalInnerVarSquareNode(LocalInnerVarReadNode):
    def execute(self, frame):
        value = read_inner(frame, self._frame_idx)
        return value.prim_multiply(value)


class UninitializedVarSquareNode(ExpressionNode):
    # it's not a quasi immutable, because we don't execute it:
    _immutable_fields_ = ["_var_read_node"]
    _child_nodes_ = ["_var_read_node"]

    def __init__(self, receiver_expr, source_section):
        ExpressionNode.__init__(self, source_section)
        self._var_read_node = receiver_expr

    def execute(self, frame):
        return self._specialize().execute(frame)

    def is_frame_access(self):
        """
        If true, then it's a basic frame access,
        and not an access to the inner part of the frame.
        """
        node = self._var_read_node
        assert isinstance(node, UninitializedReadNode)
        return not node.var.is_accessed_out_of_context()

    def get_access_idx(self):
        node = self._var_read_node
        assert isinstance(node, UninitializedReadNode)
        return node.var.access_idx

    def get_context_level(self):
        node = self._var_read_node
        assert isinstance(node, UninitializedReadNode)
        return node._context_level  # pylint: disable=protected-access

    def _specialize(self):
        node = self._var_read_node
        assert isinstance(node, UninitializedReadNode)
        return self.replace(
            node.var.get_square_node(
                node._context_level,  # pylint: disable=protected-access
                self.source_section,
            )
        )


class LocalFrameReadSquareWriteNode(ExpressionNode):
    _immutable_fields_ = ["_read_frame_idx", "_write_frame_idx"]

    def __init__(self, read_frame_idx, write_frame_idx, source_section):
        ExpressionNode.__init__(self, source_section)
        assert read_frame_idx >= 0
        assert write_frame_idx >= 0

        self._read_frame_idx = read_frame_idx
        self._write_frame_idx = write_frame_idx

    def execute(self, frame):
        value = read_frame(frame, self._read_frame_idx)
        result = value.prim_multiply(value)
        write_frame(frame, self._write_frame_idx, result)
        return result


class NonLocalReadSquareWriteNode(ExpressionNode):
    _immutable_fields_ = [
        "_read_frame_idx",
        "_read_context_level",
        "_write_frame_idx",
        "_write_context_level",
    ]

    def __init__(
        self,
        read_frame_idx,
        read_context_level,
        write_frame_idx,
        write_context_level,
        source_section,
    ):
        ExpressionNode.__init__(self, source_section)
        assert read_frame_idx >= 0
        assert read_context_level >= 0
        assert write_frame_idx >= 0
        assert write_context_level >= 0

        self._read_frame_idx = read_frame_idx
        self._read_context_level = read_context_level
        self._write_frame_idx = write_frame_idx
        self._write_context_level = write_context_level

    def handle_inlining(self, mgenc):
        raise NotImplementedError("not yet implemented")

    def handle_outer_inlined(self, removed_ctx_level, mgenc_with_inlined):
        raise NotImplementedError("not yet implemented")

    @unroll_safe
    def _determine_block(self, frame, context_level):
        assert context_level > 0

        block = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
        for _ in range(0, context_level - 1):
            block = block.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
        return block

    def execute(self, frame):
        read_block = self._determine_block(frame, self._read_context_level)
        assert isinstance(read_block, AstBlock)
        value = read_block.get_from_outer(self._read_frame_idx)
        result = value.prim_multiply(value)

        write_block = self._determine_block(frame, self._write_context_level)
        assert isinstance(write_block, AstBlock)
        write_block.set_outer(self._write_frame_idx, result)
        return result
