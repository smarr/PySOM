from __future__ import absolute_import

from som.vmobjects.array     import Array
from som.vmobjects.invokable import Invokable

from som.interpreter.bytecodes import Bytecodes

from array import array

class Method(Array, Invokable):
    
    # Static field indices and number of method fields
    NUMBER_OF_LOCALS_INDEX                 = 1 + Array.CLASS_INDEX
    MAXIMUM_NUMBER_OF_STACK_ELEMENTS_INDEX = 1 + NUMBER_OF_LOCALS_INDEX
    SIGNATURE_INDEX                        = 1 + MAXIMUM_NUMBER_OF_STACK_ELEMENTS_INDEX
    HOLDER_INDEX                           = 1 + SIGNATURE_INDEX
    NUMBER_OF_METHOD_FIELDS                = 1 + HOLDER_INDEX

    
    def __init__(self, nilObject):
        Array.__init__(self, nilObject)
        
        self._receiver_class_table   = []
        self._invoked_methods        = []
        self._receiver_class_index   = 0

        self._invocation_count       = 0

        self._bytecodes              = None
        self._inline_cache_class     = None
        self._inline_cache_invokable = None
    
    def is_primitive(self):
        return False
  
    def get_number_of_locals(self):
        # Get the number of locals (converted to a Java integer)
        return self.get_field(self.NUMBER_OF_LOCALS_INDEX)

    def set_number_of_locals(self, value):
        # Set the number of locals
        self.set_field(self.NUMBER_OF_LOCALS_INDEX, value)

    def get_maximum_number_of_stack_elements(self):
        # Get the maximum number of stack elements
        return self.get_field(self.MAXIMUM_NUMBER_OF_STACK_ELEMENTS_INDEX)
  
    def set_maximum_number_of_stack_elements(self, value):
        # Set the maximum number of stack elements
        self.set_field(self.MAXIMUM_NUMBER_OF_STACK_ELEMENTS_INDEX, value)

    def get_signature(self):
        # Get the signature of this method by reading the field with signature
        # index
        return self.get_field(self.SIGNATURE_INDEX)

    def set_signature(self, value):
        # Set the signature of this method by writing to the field with
        # signature index
        self.set_field(self.SIGNATURE_INDEX, value)

    def get_holder(self):
        # Get the holder of this method by reading the field with holder index
        return self.get_field(self.HOLDER_INDEX)

    def set_holder(self, value):
        # Set the holder of this method by writing to the field with holder index
        self.set_field(self.HOLDER_INDEX, value)

        # Make sure all nested invokables have the same holder
        for i in range(0, self.get_number_of_indexable_fields()):
            if isinstance(self.get_indexable_field(i), Invokable):
                self.get_indexable_field(i).set_holder(value)

    def get_constant(self, bytecode_index):
        # Get the constant associated to a given bytecode index
        return self.get_indexable_field(self.get_bytecode(bytecode_index + 1))

    def get_number_of_arguments(self):
        # Get the number of arguments of this method
        return self.get_signature().get_number_of_signature_arguments()
  
    def _get_default_number_of_fields(self):
        # Return the default number of fields in a method
        return self.NUMBER_OF_METHOD_FIELDS
  
    def get_number_of_bytecodes(self):
        # Get the number of bytecodes in this method
        return len(self._bytecodes)

    def set_number_of_bytecodes(self, value):
        # Set the number of bytecodes in this method
        self._bytecodes              = ["\x00"] * value
        self._inline_cache_class     = [None] * value
        self._inline_cache_invokable = [None] * value

    def get_bytecode(self, index):
        # Get the bytecode at the given index
        return self._bytecodes[index]

    def set_bytecode(self, index, value):
        # Set the bytecode at the given index to the given value
        self._bytecodes[index] = value

    # TODO: remove these things
    def increase_invocation_counter(self):
        self._invocation_count += 1

    # TODO: remove these things
    def get_invocation_count(self):
        return self._invocation_count

    def invoke(self, frame, interpreter):
        # Increase the invocation counter
        self._invocation_count += 1
    
        # Allocate and push a new frame on the interpreter stack
        new_frame = interpreter.push_new_frame(self)
        new_frame.copy_arguments_from(frame)

    def replace_bytecodes(self):
        newbc =  ["\x00"] * len(self._bytecodes)
        idx = 0

        i = 0
        while i < len(self._bytecodes):
            bc1 = self._bytecodes[i]
            len1 = Bytecodes.get_bytecode_length(bc1)

            if i + len1 >= len(self._bytecodes):
                # we're over target, so just copy bc1
                for j in range(i, i + len1):
                    newbc[idx] = self._bytecodes[j]
                    idx += 1
                break
    

            newbc[idx] = bc1
            idx += 1

            # copy args to bc1
            for j in range(i + 1, i + len1):
                newbc[idx] = self._bytecodes[j]
                idx += 1

            i += len1 # update i to point on bc2
    

        # we copy the new array because it may be shorter, and we don't
        # want to upset whatever dependence there is on the length
        self._bytecodes = array('b', [0] * idx)
        for i in range(0, idx):
            self._bytecodes[i] = newbc[i]

    # TODO: remove these things
    def get_receiver_class(self, index):
        return self._receiver_class_table[index]

    # TODO: remove these things
    def get_invoked_method(self, index):
        # return the last invoked method for a particular send
        return self._invoked_methods[index]

    # TODO: remove these things
    def add_receiver_class_and_method(self, rcvr_class, invokable):
        self._receiver_class_table.append(self._receiver_class_index, rcvr_class)
        self._invoked_methods.append(self._receiver_class_index, invokable)
        self._receiver_class_index += 1

        return self._receiver_class_index - 1

    # TODO: remove these things
    def is_receiver_class_table_full(self):
        return self._receiver_class_index == 255

    def __str__(self):
        return "Method(" + self.get_holder().get_name().get_string() + ">>" + str(self.get_signature()) + ")"

    def get_inline_cache_class(self, bytecode_index):
        return self._inline_cache_class[bytecode_index]

    def get_inline_cache_invokable(self, bytecode_index):
        return self._inline_cache_invokable[bytecode_index]

    def set_inline_cache(self, bytecode_index, receiver_class, invokable):
        self._inline_cache_class[bytecode_index]    = receiver_class
        self._inline_cache_invokable[bytecode_index] = invokable
