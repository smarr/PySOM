from rlib import jit

from som.vm.globals import nilObject


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
class Frame(object):

    _immutable_fields_ = ["_method", "_context", "_stack"]

    def __init__(self, num_elements, method, context, previous_frame):
        self._method         = method
        self._context        = context
        self._stack          = [nilObject] * num_elements
        self._stack_pointer  = method.get_initial_stack_pointer()
        self._previous_frame = previous_frame

    def get_previous_frame(self):
        return self._previous_frame

    def clear_previous_frame(self):
        self._previous_frame = None

    def has_previous_frame(self):
        return self._previous_frame is not None

    def is_bootstrap_frame(self):
        return not self.has_previous_frame()

    def get_context(self):
        return self._context

    def has_context(self):
        return self._context is not None

    @jit.unroll_safe
    def _get_context(self, level):
        """ Get the context frame at the given level """
        frame = self

        # Iterate through the context chain until the given level is reached
        for _ in range(level, 0, -1):
            frame = frame.get_context()

        # Return the found context
        return frame

    @jit.unroll_safe
    def get_outer_context(self):
        """ Compute the outer context of this frame """
        frame = self

        while frame.has_context():
            frame = frame.get_context()

        # Return the outer context
        return frame

    def top(self):
        stack_pointer = jit.promote(self._stack_pointer)
        assert 0 <= stack_pointer < len(self._stack)
        return self._stack[stack_pointer]

    def set_top(self, value):
        stack_pointer = jit.promote(self._stack_pointer)
        assert 0 <= stack_pointer < len(self._stack)
        self._stack[stack_pointer] = value

    def pop(self):
        """ Pop an object from the expression stack and return it """
        stack_pointer = jit.promote(self._stack_pointer)
        assert 0 <= stack_pointer < len(self._stack)
        self._stack_pointer = stack_pointer - 1
        result = self._stack[stack_pointer]
        self._stack[stack_pointer] = None
        assert result is not None
        return result

    def push(self, value):
        """ Push an object onto the expression stack """
        stack_pointer = jit.promote(self._stack_pointer) + 1
        assert 0 <= stack_pointer < len(self._stack)
        assert value is not None
        self._stack[stack_pointer] = value
        self._stack_pointer = stack_pointer

    def reset_stack_pointer(self):
        """ Set the stack pointer to its initial value thereby clearing
            the stack """
        # arguments are stored in front of local variables
        self._stack_pointer = self._method.get_initial_stack_pointer()

    def get_stack_element(self, index):
        # Get the stack element with the given index
        # (an index of zero yields the top element)
        result = self._stack[self._stack_pointer - index]
        assert result is not None
        return result

    def set_stack_element(self, index, value):
        # Set the stack element with the given index to the given value
        # (an index of zero yields the top element)
        self._stack[self._stack_pointer - index] = value

    def _get_local(self, index):
        return self._stack[index]

    def _set_local(self, index, value):
        self._stack[index] = value

    def get_local(self, index, context_level):
        # Get the local with the given index in the given context
        return self._get_context(context_level)._get_local(index)

    def set_local(self, index, context_level, value):
        # Set the local with the given index in the given context to the given
        # value
        assert value is not None
        self._get_context(context_level)._set_local(index, value)

    def get_argument(self, index, context_level):
        # Get the context
        context = self._get_context(context_level)

        # Get the argument with the given index
        return context._stack[index]

    def set_argument(self, index, context_level, value):
        # Get the context
        context = self._get_context(context_level)

        # Set the argument with the given index to the given value
        context._stack[index] = value

    @jit.unroll_safe
    def copy_arguments_from(self, frame, num_args):
        # copy arguments from frame:
        # - arguments are at the top of the stack of frame.
        # - copy them into the argument area of the current frame
        assert num_args == self._method.get_number_of_arguments()
        for i in range(0, num_args):
            self._stack[i] = frame.get_stack_element(num_args - 1 - i)

    @jit.unroll_safe
    def pop_old_arguments_and_push_result(self, method, result):
        num_args = method.get_number_of_arguments()
        jit.promote(self._stack_pointer)
        for i in range(self._stack_pointer - num_args, self._stack_pointer):
            self.pop()
        self.push(result)

    def print_stack_trace(self, bytecode_index):
        # Print a stack trace starting in this frame
        from som.vm.universe import std_print, std_println
        std_print(self._method.get_holder().get_name().get_embedded_string())
        std_println(" %d @ %s" % (bytecode_index,
                             self._method.get_signature().get_embedded_string()))

        if self.has_previous_frame():
            self.get_previous_frame().print_stack_trace(0)


def create_frame(previous_frame, method, context):
    return Frame(method.get_number_of_frame_elements(), method, context, previous_frame)


def create_bootstrap_frame(bootstrap_method, receiver, arguments = None):
    """Create a fake bootstrap frame with the system object on the stack"""
    bootstrap_frame = create_frame(None, bootstrap_method, None)
    bootstrap_frame.push(receiver)

    if arguments:
        bootstrap_frame.push(arguments)
    return bootstrap_frame
