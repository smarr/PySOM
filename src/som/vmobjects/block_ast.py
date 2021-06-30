from rlib import jit
from som.interpreter.ast.frame import is_on_stack, read, write

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.primitive import Primitive


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
        return self._method

    def get_from_outer(self, index):
        jit.promote(index)
        assert 0 <= index < len(self._outer)
        return read(self._outer, index)

    def set_outer(self, index, value):
        jit.promote(index)
        assert 0 <= index < len(self._outer)
        write(self._outer, index, value)

    def is_outer_on_stack(self):
        return is_on_stack(self._outer)

    def get_on_stack_marker(self):
        return self._outer

    def get_class(self, universe):
        return universe.block_classes[self._method.get_number_of_arguments()]

    class Evaluation(Primitive):

        _immutable_fields_ = ["_number_of_arguments"]

        def __init__(self, num_args, universe, invoke):
            Primitive.__init__(
                self, self._compute_signature_string(num_args), universe, invoke
            )
            self._number_of_arguments = num_args

        @staticmethod
        def _compute_signature_string(num_args):
            # Compute the signature string
            signature_string = "value"
            if num_args > 1:
                signature_string += ":"
                if num_args > 2:
                    # Add extra with: selector elements if necessary
                    signature_string += "with:" * (num_args - 2)

            # Return the signature string
            return signature_string


def block_evaluation_primitive(num_args, universe):
    return AstBlock.Evaluation(num_args, universe, _invoke)


def block_evaluate(block, args):
    method = block.get_method()
    return method.invoke(block, args)


def _invoke(ivkbl, rcvr, args):
    assert isinstance(ivkbl, AstBlock.Evaluation)
    return block_evaluate(rcvr, args)
