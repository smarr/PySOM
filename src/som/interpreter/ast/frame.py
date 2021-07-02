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
#  | OnStack         |
#  +-----------------+
#  | Receiver        |
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


def create_frame(receiver, arguments, arg_inner_access, size_frame, size_inner):
    frame = [_erase_obj(nilObject)] * size_frame
    make_sure_not_resized(frame)

    if size_inner > 0:
        inner = [_erase_obj(nilObject)] * size_inner
        make_sure_not_resized(inner)
        frame[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
        frame[_FRAME_INNER_IDX] = _erase_list(inner)

        inner[_INNER_ON_STACK_IDX] = _erase_obj(trueObject)
        inner[FRAME_AND_INNER_RCVR_IDX] = _erase_obj(receiver)
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
        arg_val = _erase_obj(arguments[arg_i])
        if arg_inner_access[arg_i]:
            inner[inner_i] = arg_val
            inner_i += 1
        else:
            frame[frame_i] = arg_val
            frame_i += 1
        arg_i += 1


def mark_as_no_longer_on_stack(inner):
    assert _unerase_obj(inner[_INNER_ON_STACK_IDX]) is trueObject
    inner[_INNER_ON_STACK_IDX] = _erase_obj(falseObject)


def is_on_stack(inner):
    return _unerase_obj(inner[_INNER_ON_STACK_IDX]) is trueObject


def read(frame_or_inner, idx):
    return _unerase_obj(frame_or_inner[idx])


def write(frame_or_inner, idx, value):
    frame_or_inner[idx] = _erase_obj(value)


def read_inner(frame, idx):
    inner = _unerase_list(frame[_FRAME_INNER_IDX])
    return _unerase_obj(inner[idx])


def write_inner(frame, idx, value):
    inner = _unerase_list(frame[_FRAME_INNER_IDX])
    inner[idx] = _erase_obj(value)


def get_inner_as_context(frame):
    return _unerase_list(frame[_FRAME_INNER_IDX])
