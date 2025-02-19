from rlib import jit

LEN_NO_ARGS = 1
LEN_ONE_ARG = 2
LEN_TWO_ARGS = 3


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

    return_field_0 = return_self + 1
    return_field_1 = return_field_0 + 1
    return_field_2 = return_field_1 + 1

    inc = return_field_2 + 1
    dec = inc + 1

    inc_field = dec + 1
    inc_field_push = inc_field + 1

    jump = inc_field_push + 1
    jump_on_true_top_nil = jump + 1
    jump_on_false_top_nil = jump_on_true_top_nil + 1
    jump_on_true_pop = jump_on_false_top_nil + 1
    jump_on_false_pop = jump_on_true_pop + 1
    jump_on_not_nil_top_top = jump_on_false_pop + 1
    jump_on_nil_top_top = jump_on_not_nil_top_top + 1
    jump_on_not_nil_pop = jump_on_nil_top_top + 1
    jump_on_nil_pop = jump_on_not_nil_pop + 1
    jump_backward = jump_on_nil_pop + 1
    jump2 = jump_backward + 1
    jump2_on_true_top_nil = jump2 + 1
    jump2_on_false_top_nil = jump2_on_true_top_nil + 1
    jump2_on_true_pop = jump2_on_false_top_nil + 1
    jump2_on_false_pop = jump2_on_true_pop + 1
    jump2_on_not_nil_top_top = jump2_on_false_pop + 1
    jump2_on_nil_top_top = jump2_on_not_nil_top_top + 1
    jump2_on_not_nil_pop = jump2_on_nil_top_top + 1
    jump2_on_nil_pop = jump2_on_not_nil_pop + 1
    jump2_backward = jump2_on_nil_pop + 1

    q_super_send_1 = jump2_backward + 1
    q_super_send_2 = q_super_send_1 + 1
    q_super_send_3 = q_super_send_2 + 1
    q_super_send_n = q_super_send_3 + 1

    push_local = q_super_send_n + 1
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
    Bytecodes.pop_field_0,
    Bytecodes.pop_field_1,
]

PUSH_BLOCK_BYTECODES = [Bytecodes.push_block, Bytecodes.push_block_no_ctx]

PUSH_CONST_BYTECODES = [
    Bytecodes.push_constant,
    Bytecodes.push_constant_0,
    Bytecodes.push_constant_1,
    Bytecodes.push_constant_2,
    Bytecodes.push_0,
    Bytecodes.push_1,
    Bytecodes.push_nil,
]

PUSH_FIELD_BYTECODES = [
    Bytecodes.push_field,
    Bytecodes.push_field_0,
    Bytecodes.push_field_1,
]

POP_FIELD_BYTECODES = [
    Bytecodes.pop_field,
    Bytecodes.pop_field_0,
    Bytecodes.pop_field_1,
]

RETURN_FIELD_BYTECODES = [
    Bytecodes.return_field_0,
    Bytecodes.return_field_1,
    Bytecodes.return_field_2,
]

JUMP_BYTECODES = [
    Bytecodes.jump,
    Bytecodes.jump_on_true_top_nil,
    Bytecodes.jump_on_true_pop,
    Bytecodes.jump_on_false_pop,
    Bytecodes.jump_on_false_top_nil,
    Bytecodes.jump_on_not_nil_top_top,
    Bytecodes.jump_on_nil_top_top,
    Bytecodes.jump_on_not_nil_pop,
    Bytecodes.jump_on_nil_pop,
    Bytecodes.jump_backward,
    Bytecodes.jump2,
    Bytecodes.jump2_on_true_top_nil,
    Bytecodes.jump2_on_true_pop,
    Bytecodes.jump2_on_false_pop,
    Bytecodes.jump2_on_false_top_nil,
    Bytecodes.jump2_on_not_nil_top_top,
    Bytecodes.jump2_on_nil_top_top,
    Bytecodes.jump2_on_not_nil_pop,
    Bytecodes.jump2_on_nil_pop,
    Bytecodes.jump2_backward,
]

FIRST_DOUBLE_BYTE_JUMP_BYTECODE = Bytecodes.jump2
NUM_SINGLE_BYTE_JUMP_BYTECODES = int(len(JUMP_BYTECODES) / 2)

RUN_TIME_ONLY_BYTECODES = [
    Bytecodes.push_frame,
    Bytecodes.push_frame_0,
    Bytecodes.push_frame_1,
    Bytecodes.push_frame_2,
    Bytecodes.push_inner,
    Bytecodes.push_inner_1,
    Bytecodes.push_inner_2,
    Bytecodes.pop_frame,
    Bytecodes.pop_frame_1,
    Bytecodes.pop_frame_2,
    Bytecodes.pop_inner,
    Bytecodes.pop_inner_0,
    Bytecodes.pop_inner_1,
    Bytecodes.pop_inner_2,
    Bytecodes.q_super_send_1,
    Bytecodes.q_super_send_2,
    Bytecodes.q_super_send_3,
    Bytecodes.q_super_send_n,
]

# These Bytecodes imply a context level of 0
# and thus, are not in blocks, because there the context level would
# be at least 1.
NOT_EXPECTED_IN_BLOCK_BYTECODES = [
    Bytecodes.halt,
    Bytecodes.push_field_0,
    Bytecodes.push_field_1,
    Bytecodes.pop_field_0,
    Bytecodes.pop_field_1,
    Bytecodes.return_self,
    Bytecodes.return_field_0,
    Bytecodes.return_field_1,
    Bytecodes.return_field_2,
]

_BYTECODE_LENGTH = [
    LEN_NO_ARGS,  # halt
    LEN_NO_ARGS,  # dup
    LEN_TWO_ARGS,  # push_frame
    LEN_TWO_ARGS,  # push_frame_0
    LEN_TWO_ARGS,  # push_frame_1
    LEN_TWO_ARGS,  # push_frame_2
    LEN_TWO_ARGS,  # push_inner
    LEN_TWO_ARGS,  # push_inner_0
    LEN_TWO_ARGS,  # push_inner_1
    LEN_TWO_ARGS,  # push_inner_2
    LEN_TWO_ARGS,  # push_field
    LEN_NO_ARGS,  # push_field_0
    LEN_NO_ARGS,  # push_field_1
    LEN_ONE_ARG,  # push_block
    LEN_ONE_ARG,  # push_block_no_ctx
    LEN_ONE_ARG,  # push_constant
    LEN_NO_ARGS,  # push_constant_0
    LEN_NO_ARGS,  # push_constant_1
    LEN_NO_ARGS,  # push_constant_2
    LEN_NO_ARGS,  # push_0
    LEN_NO_ARGS,  # push_1
    LEN_NO_ARGS,  # push_nil
    LEN_ONE_ARG,  # push_global
    LEN_NO_ARGS,  # pop
    LEN_TWO_ARGS,  # pop_frame
    LEN_TWO_ARGS,  # pop_frame_0
    LEN_TWO_ARGS,  # pop_frame_1
    LEN_TWO_ARGS,  # pop_frame_2
    LEN_TWO_ARGS,  # pop_inner
    LEN_TWO_ARGS,  # pop_inner_0
    LEN_TWO_ARGS,  # pop_inner_1
    LEN_TWO_ARGS,  # pop_inner_2
    LEN_TWO_ARGS,  # pop_field
    LEN_NO_ARGS,  # pop_field_0
    LEN_NO_ARGS,  # pop_field_1
    LEN_ONE_ARG,  # send_1
    LEN_ONE_ARG,  # send_2
    LEN_ONE_ARG,  # send_3
    LEN_ONE_ARG,  # send_n
    LEN_ONE_ARG,  # super_send
    LEN_NO_ARGS,  # return_local
    LEN_ONE_ARG,  # return_non_local
    LEN_NO_ARGS,  # return_self
    LEN_NO_ARGS,  # return_field_0
    LEN_NO_ARGS,  # return_field_1
    LEN_NO_ARGS,  # return_field_2
    LEN_NO_ARGS,  # inc
    LEN_NO_ARGS,  # dec
    LEN_TWO_ARGS,  # inc_field
    LEN_TWO_ARGS,  # inc_field_push
    LEN_TWO_ARGS,  # jump
    LEN_TWO_ARGS,  # jump_on_true_top_nil
    LEN_TWO_ARGS,  # jump_on_false_top_nil
    LEN_TWO_ARGS,  # jump_on_true_pop
    LEN_TWO_ARGS,  # jump_on_false_pop
    LEN_TWO_ARGS,  # jump_on_not_nil_top_top,
    LEN_TWO_ARGS,  # jump_on_nil_top_top,
    LEN_TWO_ARGS,  # jump_on_not_nil_pop,
    LEN_TWO_ARGS,  # jump_on_nil_pop,
    LEN_TWO_ARGS,  # jump_backward
    LEN_TWO_ARGS,  # jump2
    LEN_TWO_ARGS,  # jump2_on_true_top_nil
    LEN_TWO_ARGS,  # jump2_on_false_top_nil
    LEN_TWO_ARGS,  # jump2_on_true_pop
    LEN_TWO_ARGS,  # jump2_on_false_pop
    LEN_TWO_ARGS,  # jump2_on_not_nil_top_top,
    LEN_TWO_ARGS,  # jump2_on_nil_top_top,
    LEN_TWO_ARGS,  # jump2_on_not_nil_pop,
    LEN_TWO_ARGS,  # jump2_on_nil_pop,
    LEN_TWO_ARGS,  # jump2_backward
    LEN_ONE_ARG,  # q_super_send_1
    LEN_ONE_ARG,  # q_super_send_2
    LEN_ONE_ARG,  # q_super_send_3
    LEN_ONE_ARG,  # q_super_send_n
    # rewritten on first use
    LEN_TWO_ARGS,  # push_local
    LEN_TWO_ARGS,  # push_argument
    LEN_TWO_ARGS,  # pop_local
    LEN_TWO_ARGS,  # pop_argument
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
