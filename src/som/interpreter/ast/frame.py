from rlib import jit
from rlib.debug import make_sure_not_resized
from rlib.erased import new_erasing_pair
from som.vm.globals import nilObject, trueObject, falseObject

# Frame Design Notes
#
# The state for a method activation is constructed from one or two plain lists/arrays
# that represent the Frame and Inner.
#
# The Frame holds the receiver, any additional arguments to the method,
# and local variables;
# except for, any arguments and local variables that are accessed
# by an inner lexical scopes.
#
# The Inner holds a copy of the receiver, as well as the arguments and local variables
# accessed by the inner lexical scopes.
#
# The goal of this design is that the frame is most likely going to be "virtualized"
# by the compiler. This means, in the resulting native code after just-in-time compilation
# the frame is not actually allocated.
# Though, the Inner may need to be allocated when it escapes the compilation unit, which
# is often the case when there are nested loops, in which an outer scope, perhaps a counter
# is accessed.
#
# Note, while the Inner might not be allocated, for simplicity, the slot will always be
# reserved. This also neatly aligns the indexes for receiver access in either
# Frame or Inner.
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
#
#   Inner
#
#  +-----------------+
#  | OnStack         |  boolean indicating whether the frame is still on the stack
#  +-----------------+
#  | Receiver        |  the same as the receiver in the frame, not to be changed
#  +-----------------+
#  | ArgForInner 1   |
#  | ...             |
#  | ArgForInner n   |
#  +-----------------+
#  | LocalForInner 1 |
#  | ...             |
#  | LocalForInner n |
#  +-----------------+

_FRAME_INNER_IDX = 0

FRAME_AND_INNER_RCVR_IDX = 1
_FRAME_AND_INNER_FIRST_ARG = 2

_INNER_ON_STACK_IDX = 0


ARG_OFFSET = _FRAME_AND_INNER_FIRST_ARG

_erase_list, _unerase_list = new_erasing_pair("frame_and_inner")
_erase_obj, _unerase_obj = new_erasing_pair("abstract_obj")


def create_frame_1(receiver, size_frame, size_inner):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

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


def create_frame_2(receiver, arg, arg_inner, size_frame, size_inner):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver

        if arg_inner:
            inner[FRAME_AND_INNER_RCVR_IDX + 1] = arg
        else:
            frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg)
    else:
        frame[0] = _erase_list(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg)

    return frame


def create_frame_3(receiver, arg1, arg2, arg_inner_access, size_frame, size_inner):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver

        if arg_inner_access[0]:
            inner[FRAME_AND_INNER_RCVR_IDX + 1] = arg1
            if arg_inner_access[1]:
                inner[FRAME_AND_INNER_RCVR_IDX + 2] = arg2
            else:
                frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg2)
        else:
            frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg1)
            if arg_inner_access[1]:
                inner[FRAME_AND_INNER_RCVR_IDX + 1] = arg2
            else:
                frame[FRAME_AND_INNER_RCVR_IDX + 2] = _erase_obj(arg2)
    else:
        frame[0] = _erase_list(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[FRAME_AND_INNER_RCVR_IDX + 1] = _erase_obj(arg1)
        frame[FRAME_AND_INNER_RCVR_IDX + 2] = _erase_obj(arg2)

    return frame


def create_frame_args(receiver, arguments, arg_inner_access, size_frame, size_inner):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    if size_inner > 0:
        inner = [nilObject] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = trueObject
        inner[FRAME_AND_INNER_RCVR_IDX] = receiver
        _set_arguments_with_inner(frame, inner, arguments, arg_inner_access)
    else:
        frame[0] = _erase_obj(None)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        _set_arguments_without_inner(frame, arguments, arg_inner_access)

    return frame


@jit.unroll_safe
def _set_arguments_without_inner(frame, arguments, arg_inner_access):
    arg_i = 0
    frame_i = _FRAME_AND_INNER_FIRST_ARG

    assert len(arguments) == len(arg_inner_access)

    while arg_i < len(arg_inner_access):
        frame[frame_i] = _erase_obj(arguments[arg_i])
        frame_i += 1
        arg_i += 1


@jit.unroll_safe
def _set_arguments_with_inner(frame, inner, arguments, arg_inner_access):
    arg_i = 0
    frame_i = 2
    inner_i = _FRAME_AND_INNER_FIRST_ARG

    assert len(arguments) == len(arg_inner_access)

    while arg_i < len(arg_inner_access):
        if arg_inner_access[arg_i]:
            inner[inner_i] = arguments[arg_i]
            inner_i += 1
        else:
            frame[frame_i] = _erase_obj(arguments[arg_i])
            frame_i += 1
        arg_i += 1


def mark_as_no_longer_on_stack(inner):
    assert inner[_INNER_ON_STACK_IDX] is trueObject
    inner[_INNER_ON_STACK_IDX] = falseObject


def is_on_stack(inner):
    return inner[_INNER_ON_STACK_IDX] is trueObject


def read_frame(frame, idx):
    return _unerase_obj(frame[idx])


def write_frame(frame, idx, value):
    frame[idx] = _erase_obj(value)


def read_inner(frame, idx):
    inner = _unerase_list(frame[_FRAME_INNER_IDX])
    return inner[idx]


def write_inner(frame, idx, value):
    inner = _unerase_list(frame[_FRAME_INNER_IDX])
    inner[idx] = value


def get_inner_as_context(frame):
    return _unerase_list(frame[_FRAME_INNER_IDX])
