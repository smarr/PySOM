from rlib import jit


class Bytecodes(object):

    # Bytecodes used by the Simple Object Machine (SOM)
    halt = 0
    dup = 1
    push_local = 2
    push_argument = 3
    push_field = 4
    push_block = 5
    push_constant = 6
    push_global = 7
    pop = 8
    pop_local = 9
    pop_argument = 10
    pop_field = 11
    send = 12
    super_send = 13
    return_local = 14
    return_non_local = 15
    return_self = 16

    inc = 17
    dec = 18

    q_super_send = 19


_NUM_BYTECODES = 20

_BYTECODE_LENGTH = [
    1,  # halt
    1,  # dup
    3,  # push_local
    3,  # push_argument
    3,  # push_field
    2,  # push_block
    2,  # push_constant
    2,  # push_global
    1,  # pop
    3,  # pop_local
    3,  # pop_argument
    3,  # pop_field
    2,  # send
    2,  # super_send
    1,  # return_local
    2,  # return_non_local
    1,  # return_self
    1,  # inc
    1,  # dec
    2,  # q_super_send
]

# chose a unreasonable number to be recognizable
_STACK_EFFECT_DEPENDS_ON_MESSAGE = -1000

_BYTECODE_STACK_EFFECT = [
    0,  # halt
    1,  # dup
    1,  # push_local
    1,  # push_argument
    1,  # push_field
    1,  # push_block
    1,  # push_constant
    1,  # push_global
    -1,  # pop
    -1,  # pop_local
    -1,  # pop_argument
    -1,  # pop_field
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # send
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # super_send
    0,  # return_local
    0,  # return_non_local
    0,  # return_self
    0,  # inc
    0,  # dec
    _STACK_EFFECT_DEPENDS_ON_MESSAGE,  # q_super_send
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
