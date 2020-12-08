from rlib.jit import we_are_jitted
from .expression_node import ExpressionNode
from som.interpreter.objectstorage.field_accessor_node import create_read, \
    create_write

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object_with_layout import ObjectWithLayout


class _AbstractFieldNode(ExpressionNode):

    _immutable_fields_ = ["_self_exp?", "_field_idx"]
    _child_nodes_      = ["_self_exp"]

    def __init__(self, self_exp, field_idx, source_section):
        ExpressionNode.__init__(self, source_section)
        self._self_exp  = self.adopt_child(self_exp)
        self._field_idx = field_idx


class FieldReadNode(_AbstractFieldNode):

    _immutable_fields_ = ['_read?']
    _child_nodes_      = ['_read']

    def __init__(self, self_exp, field_idx, source_section):
        _AbstractFieldNode.__init__(self, self_exp, field_idx, source_section)
        self._read = self.adopt_child(create_read(field_idx))

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        assert isinstance(self_obj, ObjectWithLayout)
        if we_are_jitted():
            return self_obj.get_field(self._field_idx)
        else:
            return self._read.read(self_obj)


class FieldWriteNode(_AbstractFieldNode):

    _immutable_fields_ = ["_value_exp?", "_write?"]
    _child_nodes_      = ["_value_exp",  "_write"]

    def __init__(self, self_exp, value_exp, field_idx, source_section):
        _AbstractFieldNode.__init__(self, self_exp, field_idx, source_section)
        self._value_exp = self.adopt_child(value_exp)
        self._write     = self.adopt_child(create_write(field_idx))

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        value    = self._value_exp.execute(frame)
        assert isinstance(self_obj, ObjectWithLayout)
        assert isinstance(value, AbstractObject)
        if we_are_jitted():
            self_obj.set_field(self._field_idx, value)
        else:
            self._write.write(self_obj, value)
        return value


def create_read_node(self_exp, index, source_section = None):
    return FieldReadNode(self_exp, index, source_section)


def create_write_node(self_exp, value_exp, index, source_section = None):
    return FieldWriteNode(self_exp, value_exp, index, source_section)
