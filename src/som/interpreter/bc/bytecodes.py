from rlib import jit


class Bytecodes(object):

    # Bytecodes used by the Simple Object Machine (SOM)
    halt = 0
    dup = 1
    push_frame = 2
    push_inner = 3
    push_field = 4
    push_block = 5
    push_constant = 6
    push_global = 7
    pop = 8
    pop_frame = 9
    pop_inner = 10
    pop_field = 11
    send_1 = 12
    send_2 = 13
    send_3 = 14
    send_n = 15
    super_send = 16
    return_local = 17
    return_non_local = 18
    return_self = 19

    inc = 20
    dec = 21

    q_super_send_1 = 22
    q_super_send_2 = 23
    q_super_send_3 = 24
    q_super_send_n = 25

    push_local = 26
    push_argument = 27
    pop_local = 28
    pop_argument = 29


_NUM_BYTECODES = 30

_BYTECODE_LENGTH = [
    1,  # halt
    1,  # dup
    3,  # push_frame
    3,  # push_inner
    3,  # push_field
    2,  # push_block
    2,  # push_constant
    2,  # push_global
    1,  # pop
    3,  # pop_frame
    3,  # pop_inner
    3,  # pop_field
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
    1,  # push_inner
    1,  # push_field
    1,  # push_block
    1,  # push_constant
    1,  # push_global
    -1,  # pop
    -1,  # pop_frame
    -1,  # pop_inner
    -1,  # pop_field
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
