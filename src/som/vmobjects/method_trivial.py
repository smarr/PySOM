from rlib.jit import elidable_promote
from som.interpreter.bc.frame import stack_pop_old_arguments_and_push_result

from som.vmobjects.method import AbstractMethod


class AbstractTrivialMethod(AbstractMethod):
    def get_number_of_locals(self):  # pylint: disable=no-self-use
        return 0

    def get_maximum_number_of_stack_elements(self):  # pylint: disable=no-self-use
        return 0

    def set_holder(self, value):
        self._holder = value

    @elidable_promote("all")
    def get_number_of_arguments(self):
        return self._signature.get_number_of_signature_arguments()

    @elidable_promote("all")
    def get_number_of_signature_arguments(self):
        return self._signature.get_number_of_signature_arguments()


class LiteralReturn(AbstractTrivialMethod):
    def __init__(self, signature, value):
        AbstractTrivialMethod.__init__(self, signature)
        self._value = value

    def invoke_1(self, _rcvr):
        return self._value

    def invoke_2(self, _rcvr, _arg1):
        return self._value

    def invoke_3(self, _rcvr, _arg1, _arg2):
        return self._value

    def invoke_n(self, stack, stack_ptr):
        return stack_pop_old_arguments_and_push_result(
            stack,
            stack_ptr,
            self._signature.get_number_of_signature_arguments(),
            self._value,
        )
