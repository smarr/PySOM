from som.compiler.ast.variable import Argument
from som.interpreter.ast.nodes.contextual_node import ContextualNode
from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.specialized.int_inc_node import IntIncrementNode
from som.interpreter.ast.nodes.variable_node import UninitializedReadNode
from som.vmobjects.method_trivial import FieldRead, FieldWrite

MAX_FIELD_ACCESS_CHAIN_LENGTH = 6


class _AbstractFieldNode(ExpressionNode):
    _immutable_fields_ = ["_self_exp?", "field_idx"]
    _child_nodes_ = ["_self_exp"]

    def __init__(self, self_exp, field_idx, source_section):
        ExpressionNode.__init__(self, source_section)
        self._self_exp = self.adopt_child(self_exp)
        self.field_idx = field_idx


class FieldReadNode(_AbstractFieldNode):
    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        return self_obj.get_field(self.field_idx)

    def create_trivial_method(self, signature):
        if isinstance(self._self_exp, ContextualNode):
            ctx_level = self._self_exp.get_context_level()
        else:
            ctx_level = 0
        return FieldRead(signature, self.field_idx, ctx_level)


class FieldWriteNode(_AbstractFieldNode):
    _immutable_fields_ = ["_value_exp?"]
    _child_nodes_ = ["_value_exp"]

    def __init__(self, self_exp, value_exp, field_idx, source_section):
        _AbstractFieldNode.__init__(self, self_exp, field_idx, source_section)
        self._value_exp = self.adopt_child(value_exp)

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        value = self._value_exp.execute(frame)
        self_obj.set_field(self.field_idx, value)
        return value

    def create_trivial_method(self, signature):
        if isinstance(self._self_exp, ContextualNode):
            # block methods not currently supported
            return None

        val_exp = self._value_exp
        if not isinstance(val_exp, UninitializedReadNode):
            return None

        var = val_exp.var
        if isinstance(var, Argument):
            arg_idx = var.idx
            return FieldWrite(signature, self.field_idx, arg_idx)
        return None

    def is_trivial_in_sequence(self):
        return True


class FieldIncrementNode(_AbstractFieldNode):
    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        return self_obj.inc_field(self.field_idx)


def create_read_node(self_exp, index, source_section=None):
    return FieldReadNode(self_exp, index, source_section)


def create_write_node(self_exp, value_exp, index, source_section=None):
    if isinstance(value_exp, IntIncrementNode) and value_exp.does_access_field(index):
        return FieldIncrementNode(self_exp, index, source_section)
    return FieldWriteNode(self_exp, value_exp, index, source_section)
