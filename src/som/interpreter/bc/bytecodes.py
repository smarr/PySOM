from rlib import jit


class Bytecodes(object):

    # Bytecodes used by the Simple Object Machine (SOM)
    halt = 0
    dup = halt + 1

    push_frame = dup + 1
    push_frame_0 = push_frame + 1
    push_frame_1 = push_frame_0 + 1
    push_frame_2 = push_frame_1 + 1

    push_inner = push_frame_2 + 1
    push_inner_0 = push_inner + 1
    push_inner_1 = push_inner_0 + 1
    push_inner_2 = push_inner_1 + 1

    push_field = push_inner_2 + 1
    push_field_0 = push_field + 1
    push_field_1 = push_field_0 + 1

    push_block = push_field_1 + 1
    push_block_no_ctx = push_block + 1

    push_constant = push_block_no_ctx + 1
    push_constant_0 = push_constant + 1
    push_constant_1 = push_constant_0 + 1
    push_constant_2 = push_constant_1 + 1

    push_0 = push_constant_2 + 1
    push_1 = push_0 + 1
    push_nil = push_1 + 1

    push_global = push_nil + 1

    pop = push_global + 1

    pop_frame = pop + 1
    pop_frame_0 = pop_frame + 1
    pop_frame_1 = pop_frame_0 + 1
    pop_frame_2 = pop_frame_1 + 1

    pop_inner = pop_frame_2 + 1
    pop_inner_0 = pop_inner + 1
    pop_inner_1 = pop_inner_0 + 1
    pop_inner_2 = pop_inner_1 + 1

    pop_field = pop_inner_2 + 1
    pop_field_0 = pop_field + 1
    pop_field_1 = pop_field_0 + 1

    send_1 = pop_field_1 + 1
    send_2 = send_1 + 1
    send_3 = send_2 + 1
    send_n = send_3 + 1

    super_send = send_n + 1

    return_local = super_send + 1
    return_non_local = return_local + 1
    return_self = return_non_local + 1

    inc = return_self + 1
    dec = inc + 1

    q_super_send_1 = dec + 1
    q_super_send_2 = q_super_send_1 + 1
    q_super_send_3 = q_super_send_2 + 1
    q_super_send_n = q_super_send_3 + 1

    push_local = q_super_send_n + 1
    push_argument = push_local + 1
    pop_local = push_argument + 1
    pop_argument = pop_local + 1

    invalid = pop_argument + 1


_NUM_BYTECODES = Bytecodes.pop_argument + 1

POP_X_BYTECODES = [Bytecodes.pop_local, Bytecodes.pop_argument, Bytecodes.pop_field]

_BYTECODE_LENGTH = [
    1,  # halt
    1,  # dup
    3,  # push_frame
    3,  # push_frame_0
    3,  # push_frame_1
    3,  # push_frame_2
    3,  # push_inner
    3,  # push_inner_0
    3,  # push_inner_1
    3,  # push_inner_2
    3,  # push_field
    1,  # push_field_0
    1,  # push_field_1
    2,  # push_block
    2,  # push_block_no_ctx
    2,  # push_constant
    1,  # push_constant_0
    1,  # push_constant_1
    1,  # push_constant_2
    1,  # push_0
    1,  # push_1
    1,  # push_nil
    2,  # push_global
    1,  # pop
    3,  # pop_frame
    3,  # pop_frame_0
    3,  # pop_frame_1
    3,  # pop_frame_2
    3,  # pop_inner
    3,  # pop_inner_0
    3,  # pop_inner_1
    3,  # pop_inner_2
    3,  # pop_field
    1,  # pop_field_0
    1,  # pop_field_1
    2,  # send_1
    2,  # send_2
    2,  # send_3
    2,  # send_n
    2,  # super_send_1
    1,  # return_local
    2,  # return_non_local
    1,  # return_self
    1,  # inc
    1,  # dec
    2,  # q_super_send_1
    2,  # q_super_send_2
    2,  # q_super_send_3
    2,  # q_super_send_n
    # rewritten on first use
    3,  # push_local
    3,  # push_argument
    3,  # pop_local
    3,  # pop_argument
]

# chose a unreasonable number to be recognizable
_STACK_EFFECT_DEPENDS_ON_MESSAGE = -1000

_BYTECODE_STACK_EFFECT = [
    0,  # halt
    1,  # dup
    1,  # push_frame
    1,  # push_frame_0
    1,  # push_frame_1
    1,  # push_frame_2
    1,  # push_inner
    1,  # push_inner_0
    1,  # push_inner_1
    1,  # push_inner_2
    1,  # push_field
    1,  # push_field_0
    1,  # push_field_1
    1,  # push_block
    1,  # push_block_no_ctx
    1,  # push_constant
    1,  # push_constant_0
    1,  # push_constant_1
    1,  # push_constant_2
    1,  # push_0
    1,  # push_1
    1,  # push_nil
    1,  # push_global
    -1,  # pop
    -1,  # pop_frame
    -1,  # pop_frame_0
    -1,  # pop_frame_1
    -1,  # pop_frame_2
    -1,  # pop_inner
    -1,  # pop_inner_0
    -1,  # pop_inner_1
    -1,  # pop_inner_2
    -1,  # pop_field
    -1,  # pop_field_0
    -1,  # pop_field_1
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # send_1
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # send_2
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # send_3
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # send_n
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # super_send
    0,  # return_local
    0,  # return_non_local
    0,  # return_self
    0,  # inc
    0,  # dec
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # q_super_send_1
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # q_super_send_2
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # q_super_send_3
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # q_super_send_n
    1,  # push_argument
    1,  # push_field
    -1,  # pop_local
    -1,  # pop_argument
]


@jit.elidable
def bytecode_length(bytecode):
    assert 0 <= bytecode < len(_BYTECODE_LENGTH)
    return _BYTECODE_LENGTH[bytecode]


@jit.elidable
def bytecode_stack_effect(bytecode, number_of_arguments_of_message_send=0):
    assert 0 <= bytecode < len(_BYTECODE_STACK_EFFECT)
    if bytecode_stack_effect_depends_on_send(bytecode):
        # +1 in order to account for the return value
        return -number_of_arguments_of_message_send + 1
    return _BYTECODE_STACK_EFFECT[bytecode]


def bytecode_stack_effect_depends_on_send(bytecode):
    assert 0 <= bytecode < len(_BYTECODE_STACK_EFFECT)
    return _BYTECODE_STACK_EFFECT[bytecode] == _STACK_EFFECT_DEPENDS_ON_MESSAGE


@jit.elidable
def bytecode_as_str(bytecode):
    assert 0 <= bytecode < len(_BYTECODE_NAMES)
    return _BYTECODE_NAMES[bytecode]


def _sorted_bytecode_names(cls):
    "NOT_RPYTHON"
    """This function is only called a single time, at load time of this module.
       For RPypthon, this means, during translation of the module.
    """
    return [
        key.upper()
        for value, key in sorted(
            [
                (value, key)
                for key, value in cls.__dict__.items()
                if isinstance(value, int) and key[0] != "_"
            ]
        )
    ]


_BYTECODE_NAMES = _sorted_bytecode_names(Bytecodes)
