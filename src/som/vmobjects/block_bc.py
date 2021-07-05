from rlib import jit
from som.interpreter.ast.frame import is_on_stack

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.primitive import Primitive
from som.interpreter.bc.frame import get_stack_element


class BcBlock(AbstractObject):

    _immutable_fields_ = ["_method", "_outer"]

    def __init__(self, method, inner):
        AbstractObject.__init__(self)
        self._method = method
        self._outer = inner

    def is_same_context(self, other_block):
        assert isinstance(other_block, BcBlock)
        return self._outer is other_block._outer  # pylint: disable=protected-access

    def get_method(self):
        return self._method

    def get_from_outer(self, index):
        jit.promote(index)
        assert 0 <= index < len(self._outer)
        assert isinstance(self._outer[index], AbstractObject)
        return self._outer[index]

    def set_outer(self, index, value):
        jit.promote(index)
        assert 0 <= index < len(self._outer)
        assert isinstance(value, AbstractObject)
        self._outer[index] = value

    def is_outer_on_stack(self):
        # TODO: can we get rid of this?
        # we may need a second bytecode for this (push block w/o context)
        if self._outer is None:
            return True
        return is_on_stack(self._outer)

    def get_on_stack_marker(self):
        return self._outer

    def get_class(self, universe):
        return universe.block_classes[self._method.get_number_of_arguments()]


class _Evaluation(Primitive):

    _immutable_fields_ = ["_number_of_arguments"]

    def __init__(self, num_args, universe, invoke):
        Primitive.__init__(
            self, self._compute_signature_string(num_args), universe, invoke
        )
        self._number_of_arguments = num_args

    @staticmethod
    def _compute_signature_string(num_args):
        signature_string = "value"
        if num_args > 1:
            signature_string += ":"
            if num_args > 2:
                # Add extra with: selector elements if necessary
                signature_string += "with:" * (num_args - 2)

        return signature_string


def block_evaluation_primitive(num_args, universe):
    return _Evaluation(num_args, universe, _invoke)


def _invoke(ivkbl, frame):
    assert isinstance(ivkbl, _Evaluation)
    block = get_stack_element(
        frame, ivkbl._number_of_arguments - 1  # pylint: disable=W
    )
    method = block.get_method()
    method.invoke(frame)
