from rlib import jit


class Bytecodes(object):
    # Bytecodes used by the Simple Object Machine (SOM)
    halt = 0
    dup = halt + 1

    push_frame = dup + 1
    push_inner = push_frame + 1
    push_field = push_inner + 1
    push_block = push_field + 1
    push_block_no_ctx = push_block + 1
    push_constant = push_block_no_ctx + 1
    push_global = push_constant + 1

    pop = push_global + 1
    pop_frame = pop + 1
    pop_inner = pop_frame + 1
    pop_field = pop_inner + 1

    send_n = pop_field + 1
    super_send = send_n + 1

    return_local = super_send + 1
    return_non_local = return_local + 1

    push_local = return_non_local + 1
    push_argument = push_local + 1
    pop_local = push_argument + 1
    pop_argument = pop_local + 1

    invalid = pop_argument + 1


def is_one_of(bytecode, candidates):
    for c in candidates:
        if c == bytecode:
            return True
    return False


_NUM_BYTECODES = Bytecodes.pop_argument + 1

POP_X_BYTECODES = [
    Bytecodes.pop_local,
    Bytecodes.pop_argument,
    Bytecodes.pop_field,
]

PUSH_BLOCK_BYTECODES = [Bytecodes.push_block, Bytecodes.push_block_no_ctx]

PUSH_CONST_BYTECODES = [
    Bytecodes.push_constant,
]

PUSH_FIELD_BYTECODES = [
    Bytecodes.push_field,
]

POP_FIELD_BYTECODES = [
    Bytecodes.pop_field,
]

RUN_TIME_ONLY_BYTECODES = [
    Bytecodes.push_frame,
    Bytecodes.push_inner,
    Bytecodes.pop_frame,
    Bytecodes.pop_inner,
]

NOT_EXPECTED_IN_BLOCK_BYTECODES = [
    Bytecodes.halt,
]

_BYTECODE_LENGTH = [
    1,  # halt
    1,  # dup
    3,  # push_frame
    3,  # push_inner
    3,  # push_field
    2,  # push_block
    2,  # push_block_no_ctx
    2,  # push_constant
    2,  # push_global
    1,  # pop
    3,  # pop_frame
    3,  # pop_inner
    3,  # pop_field
    2,  # send_n
    2,  # super_send
    1,  # return_local
    2,  # return_non_local
    # rewritten on first use
    3,  # push_local
    3,  # push_argument
    3,  # pop_local
    3,  # pop_argument
]


@jit.elidable
def bytecode_length(bytecode):
    assert 0 <= bytecode < len(_BYTECODE_LENGTH)
    return _BYTECODE_LENGTH[bytecode]


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
