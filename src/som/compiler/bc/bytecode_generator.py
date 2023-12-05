from som.interpreter.bc.bytecodes import Bytecodes as BC


def emit_pop(mgenc):
    if not mgenc.optimize_dup_pop_pop_sequence():
        emit1(mgenc, BC.pop, -1)


def emit_push_argument(mgenc, idx, ctx):
    emit3(mgenc, BC.push_argument, idx, ctx, 1)


def emit_return_local(mgenc):
    emit1(mgenc, BC.return_local, 0)


def emit_return_non_local(mgenc):
    emit2(mgenc, BC.return_non_local, mgenc.get_max_context_level(), 0)


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


def emit_push_field_with_index(
    mgenc, field_idx, ctx_level  # pylint: disable=unused-argument
):
    emit3(mgenc, BC.push_field, field_idx, mgenc.get_max_context_level(), 1)


def emit_push_global(mgenc, glob):
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

    emit_pop_field_with_index(mgenc, field_idx, ctx_level)


def emit_pop_field_with_index(mgenc, field_idx, ctx_level):
    emit3(mgenc, BC.pop_field, field_idx, ctx_level, -1)


def emit_super_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    stack_effect = -msg.get_number_of_signature_arguments() + 1  # +1 for the result
    emit2(mgenc, BC.super_send, idx, stack_effect)


def emit_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    num_args = msg.get_number_of_signature_arguments()
    stack_effect = -num_args + 1  # +1 for the result

    emit2(mgenc, BC.send_n, idx, stack_effect)


def emit_push_constant(mgenc, lit):
    idx = mgenc.add_literal_if_absent(lit)
    emit2(mgenc, BC.push_constant, idx, 1)


def emit_push_constant_index(mgenc, lit_index):
    emit2(mgenc, BC.push_constant, lit_index, 1)


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
