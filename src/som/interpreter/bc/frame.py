from rlib import jit
from som.interpreter.ast.frame import _FrameOnStackMarker

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
@jit.unroll_safe
def copy_arguments_from(frame, num_args):
    return [frame.get_stack_element(num_args - 1 - i) for i in range(0, num_args)]


_EMPTY_LIST = []
_INITIAL_STACK_PTR = -1


class Frame(object):

    _immutable_fields_ = [
        "arguments",
        "_context",
        "stack",
        "_on_stack",
        "locals",
    ]

    def __init__(self, arguments, method, context):
        self.arguments = arguments
        self._context = context
        self.stack = [nilObject] * method.get_maximum_number_of_stack_elements()
        self._stack_pointer = _INITIAL_STACK_PTR

        num_locals = method.get_number_of_locals()
        if num_locals == 0:
            self.locals = _EMPTY_LIST
        else:
            self.locals = [nilObject] * num_locals

        self._on_stack = _FrameOnStackMarker()

    def get_context(self):
        return self._context

    def has_context(self):
        return self._context is not None

    @jit.unroll_safe
    def get_context_at(self, level):
        """Get the context frame at the given level"""
        frame = self

        # Iterate through the context chain until the given level is reached
        for _ in range(level, 0, -1):
            frame = frame.get_context()

        # Return the found context
        return frame

    @jit.unroll_safe
    def get_outer_context(self):
        """Compute the outer context of this frame"""
        frame = self

        while frame.has_context():
            frame = frame.get_context()

        # Return the outer context
        return frame

    def top(self):
        stack_pointer = jit.promote(self._stack_pointer)
        assert 0 <= stack_pointer < len(self.stack)
        return self.stack[stack_pointer]

    def set_top(self, value):
        stack_pointer = jit.promote(self._stack_pointer)
        assert 0 <= stack_pointer < len(self.stack)
        self.stack[stack_pointer] = value

    def pop(self):
        """Pop an object from the expression stack and return it"""
        stack_pointer = jit.promote(self._stack_pointer)
        assert 0 <= stack_pointer < len(self.stack)
        self._stack_pointer = stack_pointer - 1
        result = self.stack[stack_pointer]
        self.stack[stack_pointer] = None
        assert result is not None
        return result

    def push(self, value):
        """Push an object onto the expression stack"""
        stack_pointer = jit.promote(self._stack_pointer) + 1
        assert 0 <= stack_pointer < len(self.stack)
        assert value is not None
        self.stack[stack_pointer] = value
        self._stack_pointer = stack_pointer

    def reset_stack_pointer(self):
        """Set the stack pointer to its initial value thereby clearing
        the stack"""
        # arguments are stored in front of local variables
        self._stack_pointer = _INITIAL_STACK_PTR

    def get_stack_element(self, index):
        # Get the stack element with the given index
        # (an index of zero yields the top element)
        result = self.stack[self._stack_pointer - index]
        assert result is not None
        return result

    def set_stack_element(self, index, value):
        # Set the stack element with the given index to the given value
        # (an index of zero yields the top element)
        self.stack[self._stack_pointer - index] = value

    def get_local(self, index, context_level):
        # Get the local with the given index in the given context
        return self.get_context_at(context_level).locals[index]

    def set_local(self, index, context_level, value):
        # Set the local with the given index in the given context to the given
        # value
        assert value is not None
        self.get_context_at(context_level).locals[index] = value

    def get_argument(self, index, context_level):
        context = self.get_context_at(jit.promote(context_level))
        return context.arguments[jit.promote(index)]

    def set_argument(self, index, context_level, value):
        context = self.get_context_at(jit.promote(context_level))
        context.arguments[jit.promote(index)] = value

    @jit.unroll_safe
    def pop_old_arguments_and_push_result(self, method, result):
        num_args = method.get_number_of_arguments()
        stack_ptr = jit.promote(self._stack_pointer)
        for _ in range(stack_ptr - num_args, stack_ptr):
            self.pop()
        self.push(result)

    def get_on_stack_marker(self):
        return self._on_stack

    # def print_stack_trace(self, bytecode_index):
    #     # Print a stack trace starting in this frame
    #     from som.vm.universe import std_print, std_println
    #
    #     std_print(self._method.get_holder().get_name().get_embedded_string())
    #     std_println(
    #         " %d @ %s"
    #         % (bytecode_index, self._method.get_signature().get_embedded_string())
    #     )
    #
    #     if self.has_previous_frame():
    #         self.get_previous_frame().print_stack_trace(0)


def create_bootstrap_frame(bootstrap_method, receiver, arguments=None):
    """Create a fake bootstrap frame with the system object on the stack"""
    bootstrap_frame = Frame([], bootstrap_method, None)
    bootstrap_frame.push(receiver)

    if arguments:
        bootstrap_frame.push(arguments)
    return bootstrap_frame
