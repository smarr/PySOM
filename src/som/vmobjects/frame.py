from som.vmobjects.array import Array

# Frame layout:
# 
# +-----------------+
# | Arguments       | 0
# +-----------------+
# | Local Variables | <-- localOffset
# +-----------------+
# | Stack           | <-- stackPointer
# | ...             |
# +-----------------+
#
class Frame(Array):
    
    # Static field indices and number of frame fields
    NUMBER_OF_FRAME_FIELDS = Array.NUMBER_OF_OBJECT_FIELDS

    def __init__(self, nilObject, num_elements, method, context, previous_frame):
        Array.__init__(self, nilObject, num_elements)
        self._stack_pointer  = 0
        self._bytecode_index = 0
        self._local_offset   = 0
        self._method         = method
        self._context        = context
        self._previous_frame = previous_frame if previous_frame else nilObject
    
    def get_previous_frame(self):
        # Get the previous frame by reading the field with previous frame index
        return self._previous_frame

    def clear_previous_frame(self, nilObject):
        # Set the previous frame to nil
        self._previous_frame = nilObject

    def has_previous_frame(self, nilObject):
        return self._previous_frame != nilObject

    def is_bootstrap_frame(self, nilObject):
        return not self.has_previous_frame(nilObject)

    def get_context(self):
        # Get the context by reading the field with context index
        return self._context

    def has_context(self, nilObject):
        return self._context != nilObject

    def _get_context(self, level):
        # Get the context frame at the given level
        frame = self

        # Iterate through the context chain until the given level is reached
        for _ in range(level, 0, -1):
            # Get the context of the current frame
            frame = frame.get_context()

        # Return the found context
        return frame

    def get_outer_context(self, nilObject):
        # Compute the outer context of this frame
        frame = self

        # Iterate through the context chain until null is reached
        while frame.has_context(nilObject):
            frame = frame.get_context()

        # Return the outer context
        return frame

    def get_method(self):
        # Get the method by reading the field with method index
        return self._method

    def _get_default_number_of_fields(self):
        # Return the default number of fields in a frame
        return self.NUMBER_OF_FRAME_FIELDS

    def pop(self):
        # Pop an object from the expression stack and return it
        stack_pointer = self.get_stack_pointer()
        self.set_stack_pointer(stack_pointer - 1)
        return self.get_indexable_field(stack_pointer)

    def push(self, value):
        # Push an object onto the expression stack
        stack_pointer = self.get_stack_pointer() + 1
        self.set_indexable_field(stack_pointer, value)
        self.set_stack_pointer(stack_pointer)

    def get_stack_pointer(self):
        # Get the current stack pointer for this frame
        return self._stack_pointer

    def set_stack_pointer(self, value):
        # Set the current stack pointer for this frame
        self._stack_pointer = value

    def reset_stack_pointer(self):
        # arguments are stored in front of local variables
        self._local_offset = self.get_method().get_number_of_arguments()

        # Set the stack pointer to its initial value thereby clearing the stack
        self.set_stack_pointer(self._local_offset +
                self.get_method().get_number_of_locals().get_embedded_integer() - 1)

    def get_bytecode_index(self):
        # Get the current bytecode index for this frame
        return self._bytecode_index

    def set_bytecode_index(self, value):
        # Set the current bytecode index for this frame
        self._bytecode_index = value

    def get_stack_element(self, index):
        # Get the stack element with the given index
        # (an index of zero yields the top element)
        return self.get_indexable_field(self.get_stack_pointer() - index)

    def set_stack_element(self, index, value):
        # Set the stack element with the given index to the given value
        # (an index of zero yields the top element)
        self.set_indexable_field(self.get_stack_pointer() - index, value)

    def _get_local(self, index):
        return self.get_indexable_field(self._local_offset + index)

    def _set_local(self, index, value):
        self.set_indexable_field(self._local_offset + index, value)

    def get_local(self, index, context_level):
        # Get the local with the given index in the given context
        return self._get_context(context_level)._get_local(index)

    def set_local(self, index, context_level, value):
        # Set the local with the given index in the given context to the given
        # value
        self._get_context(context_level)._set_local(index, value)

    def get_argument(self, index, context_level):
        # Get the context
        context = self._get_context(context_level)

        # Get the argument with the given index
        return context.get_indexable_field(index)

    def set_argument(self, index, context_level, value):
        # Get the context
        context = self._get_context(context_level)

        # Set the argument with the given index to the given value
        context.set_indexable_field(index, value)

    def copy_arguments_from(self, frame):
        # copy arguments from frame:
        # - arguments are at the top of the stack of frame.
        # - copy them into the argument area of the current frame
        num_args = self.get_method().get_number_of_arguments()
        for i in range(0, num_args):
            self.set_indexable_field(i, frame.get_stack_element(num_args - 1 - i))

    def print_stack_trace(self, nilObject):
        # Print a stack trace starting in this frame
        from som.vm.universe import Universe
        Universe.std_print(self.get_method().get_holder().get_name().get_string())
        Universe.std_print(self.get_bytecode_index() + "@"
                           + self.get_method().get_signature().get_string())
        
        if self.has_previous_frame(nilObject):
            self.get_previous_frame().print_stack_trace(nilObject)
