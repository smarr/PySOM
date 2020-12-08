from som.interpreter.ast.nodes.variable_node import UninitializedReadNode, \
    UninitializedWriteNode, LocalSharedWriteNode, LocalUnsharedWriteNode, \
    NonLocalArgumentReadNode, NonLocalArgumentWriteNode, LocalSuperReadNode, \
    NonLocalTempReadNode, NonLocalTempWriteNode, NonLocalSuperReadNode, \
    LocalArgumentReadNode, LocalArgumentWriteNode, LocalSelfReadNode, NonLocalSelfReadNode, \
    LocalUnsharedTempReadNode, LocalSharedTempReadNode


class _Variable(object):

    def __init__(self, name):
        self._name      = name
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


class Argument(_Variable):

    _immutable_fields_ = ['_arg_idx']

    def __init__(self, name, idx):
        _Variable.__init__(self, name)
        assert name == "self" or name == "$blockSelf" or idx >= 0
        self._arg_idx = idx

    def get_read_node(self, context_level):
        self._mark_accessed(context_level)
        if context_level > 0:
            if self._name == "self":
                return NonLocalSelfReadNode(context_level, None)
            else:
                return UninitializedReadNode(self, context_level, None)
        else:
            if self._name == "self":
                return LocalSelfReadNode(None)
            else:
                return LocalArgumentReadNode(self._arg_idx, None)

    def get_write_node(self, context_level, value_expr):
        self._mark_accessed(context_level)
        if context_level > 0:
            return UninitializedWriteNode(self, context_level, value_expr, None)
        else:
            return LocalArgumentWriteNode(self._arg_idx, value_expr, None)

    def get_initialized_read_node(self, context_level, source_section):
        assert context_level > 0
        assert self._access_idx >= 0
        return NonLocalArgumentReadNode(context_level, self._access_idx,
                                        source_section)

    def get_initialized_write_node(self, context_level, value_expr, source_section):
        assert context_level > 0
        assert self._access_idx >= 0
        return NonLocalArgumentWriteNode(self._access_idx, context_level, value_expr,
                                         source_section)

    def get_argument_index(self):
        return self._arg_idx

    def get_super_read_node(self, context_level, holder_class_name,
                            on_class_side, universe):
        self._is_read = True
        if context_level > 0:
            self._is_read_out_of_context = True
            return NonLocalSuperReadNode(context_level, holder_class_name,
                                         on_class_side, universe)
        else:
            return LocalSuperReadNode(holder_class_name, on_class_side,
                                      universe, None)

    def is_self(self):
        return self._name == "self"


class Local(_Variable):

    _immutable_fields_ = ['_declaration_idx']

    def __init__(self, name, idx):
        _Variable.__init__(self, name)
        self._is_written = False
        self._is_written_out_of_context = False
        assert idx >= 0
        self._declaration_idx = idx

    def is_accessed(self):
        return _Variable.is_accessed(self) or self._is_written

    def is_accessed_out_of_context(self):
        return (_Variable.is_accessed_out_of_context(self) or
                self._is_written_out_of_context)

    def get_read_node(self, context_level):
        self._mark_accessed(context_level)
        return UninitializedReadNode(self, context_level, None)

    def get_initialized_read_node(self, context_level, source_section):
        if context_level > 0:
            return NonLocalTempReadNode(context_level, self._access_idx,
                                        source_section)
        else:
            if self.is_accessed_out_of_context():
                return LocalSharedTempReadNode(self._access_idx, source_section)
            else:
                return LocalUnsharedTempReadNode(self._access_idx,
                                                 source_section)

    def get_write_node(self, context_level, value_expr):
        self._is_written = True
        if context_level > 0:
            self._is_written_out_of_context = True
        return UninitializedWriteNode(self, context_level, value_expr, None)

    def get_initialized_write_node(self, context_level, value_expr,
                                   source_section):
        if context_level > 0:
            return NonLocalTempWriteNode(context_level, self._access_idx,
                                         value_expr, source_section)
        else:
            if self.is_accessed_out_of_context():
                return LocalSharedWriteNode(self._access_idx, value_expr,
                                            source_section)
            else:
                return LocalUnsharedWriteNode(self._access_idx, value_expr,
                                              source_section)
