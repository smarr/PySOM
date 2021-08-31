from som.interpreter.bc.bytecodes import Bytecodes as BC
from som.vm.globals import nilObject, trueObject, falseObject
from som.vm.symbols import (
    sym_nil,
    sym_true,
    sym_false,
    sym_plus,
    sym_minus,
    sym_at_put_msg,
    sym_equal,
    sym_multi,
    sym_dbl_div,
    sym_equal_equal,
    sym_is_nil,
    sym_not_nil,
    sym_at_msg,
)


def emit_inc(mgenc):
    emit1(mgenc, BC.inc, 0)


def emit_dec(mgenc):
    emit1(mgenc, BC.dec, 0)


def emit_inc_field_push(mgenc, field_idx, ctx_level):
    emit3(mgenc, BC.inc_field_push, field_idx, ctx_level, 1)


def emit_pop(mgenc):
    if not mgenc.optimize_dup_pop_pop_sequence() and not mgenc.optimize_send_pop():
        emit1(mgenc, BC.pop, -1)


def emit_push_argument(mgenc, idx, ctx):
    emit3(mgenc, BC.push_argument, idx, ctx, 1)


def emit_return_self(mgenc):
    mgenc.optimize_dup_pop_pop_sequence()
    mgenc.optimize_send_pop()
    emit1(mgenc, BC.return_self, 0)


def emit_return_local(mgenc):
    if not mgenc.optimize_return_field():
        emit1(mgenc, BC.return_local, 0)


def emit_return_non_local(mgenc):
    emit2(mgenc, BC.return_non_local, mgenc.get_max_context_level(), 0)


def emit_return_field(mgenc, field_idx):
    if field_idx == 0:
        emit1(mgenc, BC.return_field_0, 0)
        return
    if field_idx == 1:
        emit1(mgenc, BC.return_field_1, 0)
        return
    if field_idx == 2:
        emit1(mgenc, BC.return_field_2, 0)
        return
    raise NotImplementedError(
        "Don't support fields with index > 2, but got " + str(field_idx)
    )


def emit_dup(mgenc):
    emit1(mgenc, BC.dup, 1)


def emit_push_block(mgenc, block_method, with_ctx):
    idx = mgenc.add_literal_if_absent(block_method)
    emit2(mgenc, BC.push_block if with_ctx else BC.push_block_no_ctx, idx, 1)


def emit_push_local(mgenc, idx, ctx):
    emit3(mgenc, BC.push_local, idx, ctx, 1)


def emit_push_field(mgenc, field_name):
    ctx_level = mgenc.get_max_context_level()
    field_idx = mgenc.get_field_index(field_name)

    emit_push_field_with_index(mgenc, field_idx, ctx_level)


def emit_push_field_with_index(mgenc, field_idx, ctx_level):
    if ctx_level == 0:
        if field_idx == 0:
            emit1(mgenc, BC.push_field_0, 1)
            return
        if field_idx == 1:
            emit1(mgenc, BC.push_field_1, 1)
            return

    emit3(mgenc, BC.push_field, field_idx, mgenc.get_max_context_level(), 1)


def emit_push_global(mgenc, glob):
    if glob is sym_nil:
        emit_push_constant(mgenc, nilObject)
        return
    if glob is sym_true:
        emit_push_constant(mgenc, trueObject)
        return
    if glob is sym_false:
        emit_push_constant(mgenc, falseObject)
        return

    idx = mgenc.add_literal_if_absent(glob)
    # the block needs to be able to send #unknownGlobal: to self
    if not mgenc.is_global_known(glob):
        mgenc.mark_self_as_accessed_from_outer_context()
    emit2(mgenc, BC.push_global, idx, 1)


def emit_pop_argument(mgenc, idx, ctx):
    emit3(mgenc, BC.pop_argument, idx, ctx, -1)


def emit_pop_local(mgenc, idx, ctx):
    emit3(mgenc, BC.pop_local, idx, ctx, -1)


def emit_pop_field(mgenc, field_name):
    ctx_level = mgenc.get_max_context_level()
    field_idx = mgenc.get_field_index(field_name)

    if mgenc.optimize_inc_field(field_idx, ctx_level):
        return

    emit_pop_field_with_index(mgenc, field_idx, ctx_level)


def emit_pop_field_with_index(mgenc, field_idx, ctx_level):
    if ctx_level == 0:
        if field_idx == 0:
            emit1(mgenc, BC.pop_field_0, -1)
            return
        if field_idx == 1:
            emit1(mgenc, BC.pop_field_1, -1)
            return
    emit3(mgenc, BC.pop_field, field_idx, ctx_level, -1)


def emit_super_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    stack_effect = -msg.get_number_of_signature_arguments() + 1  # +1 for the result
    emit2(mgenc, BC.super_send, idx, stack_effect)


def emit_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    num_args = msg.get_number_of_signature_arguments()
    stack_effect = -num_args + 1  # +1 for the result

    if num_args == 1:
        emit2(mgenc, BC.send_1, idx, stack_effect)
    elif num_args == 2:
        emit2(mgenc, BC.send_2, idx, stack_effect)
    elif num_args == 3:
        emit2(mgenc, BC.send_3, idx, stack_effect)
    else:
        emit2(mgenc, BC.send_n, idx, stack_effect)


def emit_send_pop(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    num_args = msg.get_number_of_signature_arguments()
    stack_effect = -num_args

    if num_args == 1:
        emit2(mgenc, BC.send_1_pop, idx, stack_effect)
    elif num_args == 2:
        emit2(mgenc, BC.send_2_pop, idx, stack_effect)
    elif num_args == 3:
        emit2(mgenc, BC.send_3_pop, idx, stack_effect)
    else:
        emit2(mgenc, BC.send_n_pop, idx, stack_effect)


def emit_special_send(mgenc, msg):
    if msg is sym_plus:
        emit1(mgenc, BC.send_plus, -1)
        return True
    if msg is sym_minus:
        emit1(mgenc, BC.send_minus, -1)
        return True
    if msg is sym_multi:
        emit1(mgenc, BC.send_multi, -1)
        return True
    if msg is sym_dbl_div:
        emit1(mgenc, BC.send_dbl_div, -1)
        return True
    if msg is sym_equal:
        emit1(mgenc, BC.send_equal, -1)
        return True
    if msg is sym_equal_equal:
        emit1(mgenc, BC.send_equal_equal, -1)
        return True
    if msg is sym_is_nil:
        emit1(mgenc, BC.send_is_nil, -1)
        return True
    if msg is sym_not_nil:
        emit1(mgenc, BC.send_not_nil, -1)
        return True
    if msg is sym_at_msg:
        emit1(mgenc, BC.send_at, -1)
        return True
    if msg is sym_at_put_msg:
        emit1(mgenc, BC.send_at_put, -2)
        return True
    return False


def emit_push_constant(mgenc, lit):
    from som.vmobjects.integer import Integer

    if isinstance(lit, Integer):
        if lit.get_embedded_integer() == 0:
            emit1(mgenc, BC.push_0, 1)
            return
        if lit.get_embedded_integer() == 1:
            emit1(mgenc, BC.push_1, 1)
            return

    if lit is nilObject:
        emit1(mgenc, BC.push_nil, 1)
        return

    idx = mgenc.add_literal_if_absent(lit)
    if idx == 0:
        emit1(mgenc, BC.push_constant_0, 1)
        return
    if idx == 1:
        emit1(mgenc, BC.push_constant_1, 1)
        return
    if idx == 2:
        emit1(mgenc, BC.push_constant_2, 1)
        return

    emit2(mgenc, BC.push_constant, idx, 1)


def emit_push_constant_index(mgenc, lit_index):
    emit2(mgenc, BC.push_constant, lit_index, 1)


def emit_jump_on_bool_with_dummy_offset(mgenc, is_if_true, needs_pop):
    # Remember: true and false seem flipped here.
    # This is because if the test passes, the block is inlined directly.
    # But if the test fails, we need to jump.
    # Thus, an  `#ifTrue:` needs to generated a jump_on_false.
    if needs_pop:
        bc = BC.jump_on_false_pop if is_if_true else BC.jump_on_true_pop
        stack_effect = -1
    else:
        bc = BC.jump_on_false_top_nil if is_if_true else BC.jump_on_true_top_nil
        stack_effect = 0

    emit1(mgenc, bc, stack_effect)
    idx = mgenc.add_bytecode_argument_and_get_index(0)
    mgenc.add_bytecode_argument(0)
    return idx


def emit_jump_with_dummy_offset(mgenc):
    emit1(mgenc, BC.jump, 0)
    idx = mgenc.add_bytecode_argument_and_get_index(0)
    mgenc.add_bytecode_argument(0)
    return idx


def emit_jump_backward_with_offset(mgenc, offset):
    emit3(
        mgenc,
        BC.jump_backward if offset <= 0xFF else BC.jump2_backward,
        offset & 0xFF,
        offset >> 8,
        0,
    )


def emit1(mgenc, code, stack_effect):
    mgenc.add_bytecode(code, stack_effect)


def emit2(mgenc, code, idx, stack_effect):
    mgenc.add_bytecode(code, stack_effect)
    mgenc.add_bytecode_argument(idx)


def emit2_with_dummy(mgenc, code, stack_effect):
    mgenc.add_bytecode(code, stack_effect)
    return mgenc.add_bytecode_argument_and_get_index(0)


def emit3(mgenc, code, idx, ctx, stack_effect):
    mgenc.add_bytecode(code, stack_effect)
    mgenc.add_bytecode_argument(idx)
    mgenc.add_bytecode_argument(ctx)


def emit3_with_dummy(mgenc, code, stack_effect):
    mgenc.add_bytecode(code, stack_effect)
    idx = mgenc.add_bytecode_argument_and_get_index(0)
    mgenc.add_bytecode_argument(0)
    return idx


def compute_offset(byte1, byte2):
    return byte1 + (byte2 << 8)
