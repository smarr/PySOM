from rlib.jit import promote
from som.interpreter.ast.frame import is_on_stack

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive

VALUE_SIGNATURE = [
    "UNUSED",  # there aren't any 0-arg methods/blocks
    "value",
    "value:",
    "value:with:",
]


class AstBlock(AbstractObject):

    _immutable_fields_ = ["_method", "_outer"]

    def __init__(self, method, context_values):
        AbstractObject.__init__(self)
        self._method = method
        self._outer = context_values

    def is_same_context(self, other_block):
        assert isinstance(other_block, AstBlock)
        return self._outer is other_block._outer  # pylint: disable=protected-access

    def get_method(self):
        return promote(self._method)

    def get_from_outer(self, index):
        promote(index)
        assert 0 <= index < len(self._outer)
        return self._outer[index]

    def set_outer(self, index, value):
        promote(index)
        assert 0 <= index < len(self._outer)
        self._outer[index] = value

    def is_outer_on_stack(self):
        return is_on_stack(self._outer)

    def get_on_stack_marker(self):
        return self._outer

    def get_class(self, universe):
        return universe.block_classes[self._method.get_number_of_arguments()]

    def get_object_layout(self, universe):
        return universe.block_layouts[self._method.get_number_of_arguments()]


def block_evaluation_primitive(num_args):
    if num_args == 1:
        return UnaryPrimitive(VALUE_SIGNATURE[num_args], _invoke_1)
    if num_args == 2:
        return BinaryPrimitive(VALUE_SIGNATURE[num_args], _invoke_2)
    if num_args == 3:
        return TernaryPrimitive(VALUE_SIGNATURE[num_args], _invoke_3)
    raise Exception("Unsupported number of arguments for block: " + str(num_args))


def _invoke_1(rcvr):
    return rcvr.get_method().invoke_1(rcvr)


def _invoke_2(rcvr, arg):
    return rcvr.get_method().invoke_2(rcvr, arg)


def _invoke_3(rcvr, arg1, arg2):
    return rcvr.get_method().invoke_3(rcvr, arg1, arg2)
