from rlib import jit
from rlib.debug import make_sure_not_resized
from rlib.erased import new_erasing_pair

from som.vm.globals import nilObject, trueObject
from som.interpreter.ast.frame import (
    _erase_obj,
    _unerase_obj,
    _erase_list,
    FRAME_AND_INNER_RCVR_IDX,
    _FRAME_INNER_IDX,
    _INNER_ON_STACK_IDX,
    _FRAME_AND_INNER_FIRST_ARG,
    read_frame,
)

_erase_sptr, _unerase_sptr = new_erasing_pair("stack_ptr")


class _StackPtr(object):
    def __init__(self, val):
        self.stack_ptr = val

    def __str__(self):
        return "SPtr(" + str(self.stack_ptr) + ")"


# Frame Design Notes
#
# The design of the frame for the bytecode-based interpreters is pretty much the
# same as the design for the AST-based interpreter.
# The only difference is that we reserve space for the stack at the end of the Frame.
# The design of Inner remains unchanged.
#
#   Frame
#
#  +-----------+
#  | Inner     | (Optional: for args/vars accessed from inner scopes, and non-local returns)
#  +-----------+
#  | Receiver  |
#  +-----------+
#  | Arg 1     |
#  | ...       |
#  | Arg n     |
#  +-----------+
#  | Local 1   |
#  | ...       |
#  | Local n   |
#  +-----------+
#  | Stack     | <-- stackPtr
#  | ...       |
#  +-----------+
#  | StackPtr  |
#  +-----------+


def create_frame(
    arg_inner_access_reversed,
    size_frame,
    size_inner,
    before_stack_start,
    prev_frame,
    num_args,
):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    frame[-1] = _erase_sptr(_StackPtr(before_stack_start))

    receiver = get_stack_element(prev_frame, num_args - 1)
    assert num_args - 1 == len(arg_inner_access_reversed)  # num_args without rcvr

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver
        _set_arguments_with_inner(
            frame, inner, arg_inner_access_reversed, prev_frame, num_args - 1
        )
    else:
        frame[0] = _erase_list(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        _set_arguments_without_inner(frame, prev_frame, num_args - 1)

    return frame


def create_frame_1(size_frame, size_inner, before_stack_start, receiver):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    frame[-1] = _erase_sptr(_StackPtr(before_stack_start))

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver
    else:
        frame[0] = _erase_list(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)

    return frame


def create_frame_2(
    arg_inner, size_frame, size_inner, before_stack_start, receiver, arg1
):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    frame[-1] = _erase_sptr(_StackPtr(before_stack_start))

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver
        if arg_inner:
            inner[FRAME_AND_INNER_RCVR_IDX + 1] = arg1
        else:
            frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg1)
    else:
        frame[0] = _erase_list(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg1)

    return frame


def create_frame_3(
    arg_inner_access_reversed,
    size_frame,
    size_inner,
    before_stack_start,
    receiver,
    arg1,
    arg2,
):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    frame[-1] = _erase_sptr(_StackPtr(before_stack_start))

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver
        if arg_inner_access_reversed[1]:
            inner[FRAME_AND_INNER_RCVR_IDX + 1] = arg1
            if arg_inner_access_reversed[0]:
                inner[FRAME_AND_INNER_RCVR_IDX + 2] = arg2
            else:
                frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg2)
        else:
            frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg1)
            if arg_inner_access_reversed[0]:
                inner[FRAME_AND_INNER_RCVR_IDX + 1] = arg2
            else:
                frame[FRAME_AND_INNER_RCVR_IDX + 2] = _erase_obj(arg2)
    else:
        frame[0] = _erase_list(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg1)
        frame[FRAME_AND_INNER_RCVR_IDX + 2] = _erase_obj(arg2)

    return frame


@jit.unroll_safe
def _set_arguments_without_inner(frame, prev_frame, num_args_without_rcvr):
    arg_i = num_args_without_rcvr - 1
    frame_i = _FRAME_AND_INNER_FIRST_ARG

    while arg_i >= 0:
        frame[frame_i] = _erase_obj(get_stack_element(prev_frame, arg_i))
        frame_i += 1
        arg_i -= 1


@jit.unroll_safe
def _set_arguments_with_inner(
    frame, inner, arg_inner_access_reversed, prev_frame, num_args_without_rcvr
):
    arg_i = num_args_without_rcvr - 1
    frame_i = 2
    inner_i = _FRAME_AND_INNER_FIRST_ARG

    while arg_i >= 0:
        arg_val = get_stack_element(prev_frame, arg_i)
        if arg_inner_access_reversed[arg_i]:
            inner[inner_i] = arg_val
            inner_i += 1
        else:
            frame[frame_i] = _erase_obj(arg_val)
            frame_i += 1
        arg_i -= 1


def stack_top(frame):
    stack_pointer = jit.promote(_unerase_sptr(frame[-1]).stack_ptr)
    assert stack_pointer < len(frame) - 1

    return _unerase_obj(frame[stack_pointer])


def stack_set_top(frame, value):
    stack_pointer = _unerase_sptr(frame[-1]).stack_ptr
    assert stack_pointer < len(frame) - 1

    frame[stack_pointer] = _erase_obj(value)


def stack_pop(frame):
    """Pop an object from the expression stack and return it"""
    sptr = _unerase_sptr(frame[-1])
    stack_pointer = jit.promote(sptr.stack_ptr)
    assert stack_pointer < len(frame) - 1

    sptr.stack_ptr = stack_pointer - 1
    result = _unerase_obj(frame[stack_pointer])
    frame[stack_pointer] = _erase_obj(None)
    assert result is not None
    return result


def stack_push(frame, value):
    """Push an object onto the expression stack"""
    sptr = _unerase_sptr(frame[-1])
    stack_pointer = jit.promote(sptr.stack_ptr + 1)
    assert stack_pointer < len(frame) - 1

    assert value is not None
    frame[stack_pointer] = _erase_obj(value)
    sptr.stack_ptr = stack_pointer


@jit.unroll_safe
def stack_pop_old_arguments_and_push_result(frame, num_args, result):
    for _ in range(num_args):
        stack_pop(frame)
    stack_push(frame, result)


def stack_reset_stack_pointer(frame, before_stack_start):
    """Set the stack pointer to its initial value thereby clearing
    the stack"""
    _unerase_sptr(frame[-1]).stack_ptr = before_stack_start
    assert before_stack_start < len(frame) - 1


def get_stack_element(frame, index):
    # Get the stack element with the given index
    # (an index of zero yields the top element)
    stack_pointer = _unerase_sptr(frame[-1]).stack_ptr

    result = _unerase_obj(frame[stack_pointer - index])
    assert result is not None
    return result


def set_stack_element(frame, index, value):
    # Set the stack element with the given index to the given value
    # (an index of zero yields the top element)
    stack_pointer = _unerase_sptr(frame[-1]).stack_ptr
    frame[stack_pointer - index] = _erase_obj(value)


@jit.unroll_safe
def get_block_at(frame, ctx_level):
    assert ctx_level > 0

    block = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
    for _ in range(0, ctx_level - 1):
        block = block.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
    return block


@jit.unroll_safe
def get_self_dynamically(frame):
    from som.vmobjects.block_bc import BcBlock
    from som.vmobjects.abstract_object import AbstractObject

    rcvr = read_frame(frame, FRAME_AND_INNER_RCVR_IDX)
    assert isinstance(rcvr, AbstractObject)

    while isinstance(rcvr, BcBlock):
        rcvr = rcvr.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
        assert isinstance(rcvr, AbstractObject)

    return rcvr


def create_bootstrap_frame(receiver, arguments=None):
    """Create a fake bootstrap frame with the system object on the stack"""
    bootstrap_frame = [_erase_obj(nilObject)] * (
        1 + 2 + 1
    )  # Inner + 2 stack elements + StackPtr
    bootstrap_frame[0] = _erase_list([trueObject])
    bootstrap_frame[-1] = _erase_sptr(_StackPtr(0))

    stack_push(bootstrap_frame, receiver)

    if arguments:
        stack_push(bootstrap_frame, arguments)
    return bootstrap_frame
