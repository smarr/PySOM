from rlib import jit

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.primitive import Primitive


class AstBlock(AbstractObject):

    _immutable_fields_ = ["_method", "_outer_rcvr", '_outer_args[*]',
                          '_outer_tmps']

    def __init__(self, method, context_values):
        AbstractObject.__init__(self)
        self._method         = method
        self._outer_rcvr     = context_values[0]
        self._outer_args     = context_values[1]
        self._outer_tmps     = context_values[2]
        self._outer_on_stack = context_values[3]

    def is_same_context(self, other_block):
        assert isinstance(other_block, AstBlock)
        return (self._outer_rcvr == other_block._outer_rcvr and
                self._outer_args == other_block._outer_args and
                self._outer_tmps == other_block._outer_tmps and
                self._outer_on_stack == other_block._outer_on_stack)

    def get_method(self):
        return jit.promote(self._method)

    def get_context_argument(self, index):
        jit.promote(index)
        args = self._outer_args
        assert 0 <= index < len(args)
        assert args is not None
        return args[index]

    def set_context_argument(self, index, value):
        jit.promote(index)
        args = self._outer_args
        assert 0 <= index < len(args)
        assert args is not None
        args[index] = value

    def get_context_temp(self, index):
        jit.promote(index)
        temps = self._outer_tmps
        assert 0 <= index < len(temps)
        assert temps is not None
        return temps[index]

    def set_context_temp(self, index, value):
        jit.promote(index)
        temps = self._outer_tmps
        assert 0 <= index < len(temps)
        assert temps is not None
        temps[index] = value

    def is_outer_on_stack(self):
        return self._outer_on_stack.is_on_stack()

    def get_on_stack_marker(self):
        return self._outer_on_stack

    def get_outer_self(self):
        return self._outer_rcvr

    def get_class(self, universe):
        return universe.blockClasses[self._method.get_number_of_arguments()]

    class Evaluation(Primitive):

        _immutable_fields_ = ['_number_of_arguments']

        def __init__(self, num_args, universe, invoke):
            Primitive.__init__(self, self._compute_signature_string(num_args),
                               universe, invoke)
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
