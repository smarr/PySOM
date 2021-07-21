from som.interpreter.bc.bytecodes import Bytecodes as BC


def emit_inc(mgenc):
    _emit1(mgenc, BC.inc)


def emit_dec(mgenc):
    _emit1(mgenc, BC.dec)


def emit_pop(mgenc):
    _emit1(mgenc, BC.pop)


def emit_push_argument(mgenc, idx, ctx):
    _emit3(mgenc, BC.push_argument, idx, ctx)


def emit_return_self(mgenc):
    _emit1(mgenc, BC.return_self)


def emit_return_local(mgenc):
    _emit1(mgenc, BC.return_local)


def emit_return_non_local(mgenc):
    _emit2(mgenc, BC.return_non_local, mgenc.get_max_context_level())


def emit_dup(mgenc):
    _emit1(mgenc, BC.dup)


def emit_push_block(mgenc, block_method, with_ctx):
    _emit2(
        mgenc,
        BC.push_block if with_ctx else BC.push_block_no_ctx,
        mgenc.find_literal_index(block_method),
    )


def emit_push_local(mgenc, idx, ctx):
    _emit3(mgenc, BC.push_local, idx, ctx)


def emit_push_field(mgenc, field_name):
    ctx_level = mgenc.get_max_context_level()
    field_idx = mgenc.get_field_index(field_name)

    if ctx_level == 0:
        if field_idx == 0:
            _emit1(mgenc, BC.push_field_0)
            return
        if field_idx == 1:
            _emit1(mgenc, BC.push_field_1)
            return

    _emit3(
        mgenc,
        BC.push_field,
        mgenc.get_field_index(field_name),
        mgenc.get_max_context_level(),
    )


def emit_push_global(mgenc, glob):
    # the block needs to be able to send #unknownGlobal: to self
    if not mgenc.is_global_known(glob):
        mgenc.mark_self_as_accessed_from_outer_context()
    _emit2(mgenc, BC.push_global, mgenc.find_literal_index(glob))


def emit_pop_argument(mgenc, idx, ctx):
    _emit3(mgenc, BC.pop_argument, idx, ctx)


def emit_pop_local(mgenc, idx, ctx):
    _emit3(mgenc, BC.pop_local, idx, ctx)


def emit_pop_field(mgenc, field_name):
    ctx_level = mgenc.get_max_context_level()
    field_idx = mgenc.get_field_index(field_name)

    if ctx_level == 0:
        if field_idx == 0:
            _emit1(mgenc, BC.pop_field_0)
            return
        if field_idx == 1:
            _emit1(mgenc, BC.pop_field_1)
            return
    _emit3(
        mgenc,
        BC.pop_field,
        field_idx,
        ctx_level,
    )


def emit_super_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    _emit2(mgenc, BC.super_send, idx)


def emit_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    num_args = msg.get_number_of_signature_arguments()
    if num_args == 1:
        _emit2(mgenc, BC.send_1, idx)
    elif num_args == 2:
        _emit2(mgenc, BC.send_2, idx)
    elif num_args == 3:
        _emit2(mgenc, BC.send_3, idx)
    else:
        _emit2(mgenc, BC.send_n, idx)


def emit_push_constant(mgenc, lit):
    _emit2(mgenc, BC.push_constant, mgenc.find_literal_index(lit))


def emit_push_constant_index(mgenc, lit_index):
    _emit2(mgenc, BC.push_constant, lit_index)


def _emit1(mgenc, code):
    mgenc.add_bytecode(code)


def _emit2(mgenc, code, idx):
    mgenc.add_bytecode(code)
    mgenc.add_bytecode(idx)


def _emit3(mgenc, code, idx, ctx):
    mgenc.add_bytecode(code)
    mgenc.add_bytecode(idx)
    mgenc.add_bytecode(ctx)
