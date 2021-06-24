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


def emit_push_block(mgenc, block_method):
    _emit2(mgenc, BC.push_block, mgenc.find_literal_index(block_method))


def emit_push_local(mgenc, idx, ctx):
    _emit3(mgenc, BC.push_local, idx, ctx)


def emit_push_field(mgenc, field_name):
    _emit3(
        mgenc,
        BC.push_field,
        mgenc.get_field_index(field_name),
        mgenc.get_max_context_level(),
    )


def emit_push_global(mgenc, glob):
    _emit2(mgenc, BC.push_global, mgenc.find_literal_index(glob))


def emit_pop_argument(mgenc, idx, ctx):
    _emit3(mgenc, BC.pop_argument, idx, ctx)


def emit_pop_local(mgenc, idx, ctx):
    _emit3(mgenc, BC.pop_local, idx, ctx)


def emit_pop_field(mgenc, field_name):
    _emit3(
        mgenc,
        BC.pop_field,
        mgenc.get_field_index(field_name),
        mgenc.get_max_context_level(),
    )


def emit_super_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    _emit2(mgenc, BC.super_send, idx)


def emit_send(mgenc, msg):
    idx = mgenc.add_literal_if_absent(msg)
    _emit2(mgenc, BC.send, idx)


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
