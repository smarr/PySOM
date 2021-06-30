from som.interpreter.ast.frame import FRAME_AND_INNER_RCVR_IDX
from som.interpreter.ast.nodes.variable_node import (
    UninitializedReadNode,
    UninitializedWriteNode,
    NonLocalVariableReadNode,
    LocalInnerVarReadNode,
    LocalFrameVarReadNode,
    NonLocalVariableWriteNode,
    LocalInnerVarWriteNode,
    LocalFrameVarWriteNode,
)


class _Variable(object):
    def __init__(self, name):
        self._name = name
        self._is_accessed = False
        self._is_accessed_out_of_context = False
        self._access_idx = -1

    def set_access_index(self, value):
        assert value >= 0
        self._access_idx = value

    def is_accessed(self):
        return self._is_accessed

    def is_accessed_out_of_context(self):
        return self._is_accessed_out_of_context

    def _mark_accessed(self, context_level):
        self._is_accessed = True
        if context_level > 0:
            self._is_accessed_out_of_context = True

    def get_read_node(self, context_level):
        self._mark_accessed(context_level)
        return UninitializedReadNode(self, context_level, None)

    def get_write_node(self, context_level, value_expr):
        self._mark_accessed(context_level)
        return UninitializedWriteNode(self, context_level, value_expr, None)

    def get_initialized_read_node(self, context_level, source_section):
        assert self._access_idx >= 0
        if context_level > 0:
            return NonLocalVariableReadNode(
                context_level, self._access_idx, source_section
            )
        if self.is_accessed_out_of_context():
            return LocalInnerVarReadNode(self._access_idx, source_section)
        return LocalFrameVarReadNode(self._access_idx, source_section)

    def get_initialized_write_node(self, context_level, value_expr, source_section):
        assert self._access_idx >= 0
        if context_level > 0:
            return NonLocalVariableWriteNode(
                context_level, self._access_idx, value_expr, source_section
            )
        if self.is_accessed_out_of_context():
            return LocalInnerVarWriteNode(self._access_idx, value_expr, source_section)
        return LocalFrameVarWriteNode(self._access_idx, value_expr, source_section)


class Argument(_Variable):

    _immutable_fields_ = ["_arg_idx"]

    def __init__(self, name, idx):
        _Variable.__init__(self, name)
        assert name == "self" or name == "$blockSelf" or idx >= 0
        self._arg_idx = idx

    def get_argument_index(self):
        return self._arg_idx

    def is_self(self):
        return self._name == "self"

    def get_read_node(self, context_level):
        if self._name == "self" or self._name == "$blockSelf":
            self._mark_accessed(context_level)
            if context_level > 0:
                return NonLocalVariableReadNode(
                    context_level, FRAME_AND_INNER_RCVR_IDX, None
                )
            return LocalFrameVarReadNode(FRAME_AND_INNER_RCVR_IDX, None)
        return _Variable.get_read_node(self, context_level)

    def get_initialized_read_node(self, context_level, source_section):
        if self._name == "self" or self._name == "$blockSelf":
            if context_level > 0:
                return NonLocalVariableReadNode(
                    context_level, FRAME_AND_INNER_RCVR_IDX, source_section
                )
            return LocalFrameVarReadNode(FRAME_AND_INNER_RCVR_IDX, source_section)
        return _Variable.get_initialized_read_node(self, context_level, source_section)


class Local(_Variable):

    _immutable_fields_ = ["_declaration_idx"]

    def __init__(self, name, idx):
        _Variable.__init__(self, name)

        assert idx >= 0
        self._declaration_idx = idx
