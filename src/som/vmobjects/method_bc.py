from __future__ import absolute_import

from rlib import jit

from som.interpreter.bc.frame import create_frame
from som.interpreter.control_flow import ReturnException
from som.vmobjects.abstract_object import AbstractObject


class BcMethod(AbstractObject):

    _immutable_fields_ = ["_bytecodes[*]",
                          "_literals[*]",
                          "_inline_cache_class",
                          "_inline_cache_invokable",
                          "_receiver_class_table",
                          "_number_of_locals",
                          "_maximum_number_of_stack_elements",
                          "_signature",
                          "_number_of_arguments",
                          "_initial_stack_pointer",
                          "_number_of_frame_elements",
                          "_holder"]

    def __init__(self, literals, num_locals, max_stack_elements,
                 num_bytecodes, signature):
        AbstractObject.__init__(self)

        # Set the number of bytecodes in this method
        self._bytecodes              = ["\x00"] * num_bytecodes
        self._inline_cache_class     = [None]   * num_bytecodes
        self._inline_cache_invokable = [None]   * num_bytecodes

        self._literals               = literals

        self._number_of_locals       = num_locals
        self._maximum_number_of_stack_elements = max_stack_elements
        self._signature = signature
        self._number_of_arguments = signature.get_number_of_signature_arguments()
        self._initial_stack_pointer = self._number_of_arguments + num_locals - 1
        self._number_of_frame_elements = (self._number_of_arguments + num_locals
                                          + max_stack_elements + 2)

        self._holder = None

    @staticmethod
    def is_primitive():
        return False

    @staticmethod
    def is_invokable():
        """ We use this method to identify methods and primitives """
        return True

    def get_initial_stack_pointer(self):
        return self._initial_stack_pointer

    def get_number_of_locals(self):
        # Get the number of locals
        return self._number_of_locals

    def get_maximum_number_of_stack_elements(self):
        # Get the maximum number of stack elements
        return self._maximum_number_of_stack_elements

    # XXX this means that the JIT doesn't see changes to the method object
    @jit.elidable_promote('all')
    def get_signature(self):
        return self._signature

    def get_holder(self):
        return self._holder

    def set_holder(self, value):
        self._holder = value

        # Make sure all nested invokables have the same holder
        for i in range(0, len(self._literals)):
            obj = self._literals[i]
            assert isinstance(obj, AbstractObject)
            if obj.is_invokable():
                obj.set_holder(value)

    # XXX this means that the JIT doesn't see changes to the constants
    @jit.elidable_promote('all')
    def get_constant(self, bytecode_index):
        # Get the constant associated to a given bytecode index
        return self._literals[self.get_bytecode(bytecode_index + 1)]

    @jit.elidable_promote('all')
    def get_number_of_arguments(self):
        return self._number_of_arguments

    def get_number_of_bytecodes(self):
        # Get the number of bytecodes in this method
        return len(self._bytecodes)

    @jit.elidable_promote('all')
    def get_number_of_frame_elements(self):
        # Compute the maximum number of stack locations (including arguments,
        # locals and extra buffer to support doesNotUnderstand) and set the
        # number of indexable fields accordingly
        return self._number_of_frame_elements

    @jit.elidable_promote('all')
    def get_bytecode(self, index):
        # Get the bytecode at the given index
        assert 0 <= index and index < len(self._bytecodes)
        return ord(self._bytecodes[index])

    def set_bytecode(self, index, value):
        # Set the bytecode at the given index to the given value
        assert 0 <= value and value <= 255
        self._bytecodes[index] = chr(value)

    def invoke(self, frame, interpreter):
        # Allocate and push a new frame on the interpreter stack
        new_frame = create_frame(frame, self, None)
        new_frame.copy_arguments_from(frame, self._number_of_arguments)

        try:
            result = interpreter.interpret(self, new_frame)
            frame.pop_old_arguments_and_push_result(self, result)
            new_frame.clear_previous_frame()
            return
        except ReturnException as e:
            if e.has_reached_target(new_frame):
                frame.pop_old_arguments_and_push_result(self, e.get_result())
                return
            else:
                new_frame.clear_previous_frame()
                raise e

    def __str__(self):
        return ("Method(" + self.get_holder().get_name().get_embedded_string() + ">>" +
                str(self.get_signature()) + ")")

    def get_class(self, universe):
        return universe.methodClass

    @jit.elidable
    def get_inline_cache_class(self, bytecode_index):
        assert 0 <= bytecode_index and bytecode_index < len(self._inline_cache_class)
        return self._inline_cache_class[bytecode_index]

    @jit.elidable
    def get_inline_cache_invokable(self, bytecode_index):
        assert 0 <= bytecode_index and bytecode_index < len(self._inline_cache_invokable)
        return self._inline_cache_invokable[bytecode_index]

    def set_inline_cache(self, bytecode_index, receiver_class, invokable):
        self._inline_cache_class[bytecode_index]    = receiver_class
        self._inline_cache_invokable[bytecode_index] = invokable

    def merge_point_string(self):
        """ debug info for the jit """
        return "%s>>%s" % (self.get_holder().get_name().get_embedded_string(),
                           self.get_signature().get_embedded_string())
