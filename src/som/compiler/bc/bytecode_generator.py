from som.interpreter.bc.bytecodes import Bytecodes as BC


class BytecodeGenerator(object):

    def emitINC(self, mgenc):
        self._emit1(mgenc, BC.inc)

    def emitDEC(self, mgenc):
        self._emit1(mgenc, BC.dec)

    def emitPOP(self, mgenc):
        self._emit1(mgenc, BC.pop)

    def emitPUSHARGUMENT(self, mgenc, idx, ctx):
        self._emit3(mgenc, BC.push_argument, idx, ctx)

    def emitRETURNSELF(self, mgenc):
        self._emit1(mgenc, BC.return_self)

    def emitRETURNLOCAL(self, mgenc):
        self._emit1(mgenc, BC.return_local)

    def emitRETURNNONLOCAL(self, mgenc):
        self._emit2(mgenc, BC.return_non_local, mgenc.get_max_context_level())

    def emitDUP(self, mgenc):
        self._emit1(mgenc, BC.dup)

    def emitPUSHBLOCK(self, mgenc, block_method):
        self._emit2(mgenc, BC.push_block, mgenc.find_literal_index(block_method))

    def emitPUSHLOCAL(self, mgenc, idx, ctx):
        self._emit3(mgenc, BC.push_local, idx, ctx)

    def emitPUSHFIELD(self, mgenc, field_name):
        self._emit3(mgenc, BC.push_field,
                    mgenc.get_field_index(field_name), mgenc.get_max_context_level())

    def emitPUSHGLOBAL(self, mgenc, glob):
        self._emit2(mgenc, BC.push_global, mgenc.find_literal_index(glob))

    def emitPOPARGUMENT(self, mgenc, idx, ctx):
        self._emit3(mgenc, BC.pop_argument, idx, ctx)

    def emitPOPLOCAL(self, mgenc, idx, ctx):
        self._emit3(mgenc, BC.pop_local, idx, ctx)

    def emitPOPFIELD(self, mgenc, field_name):
        self._emit3(mgenc, BC.pop_field,
                    mgenc.get_field_index(field_name), mgenc.get_max_context_level())

    def emitSUPERSEND(self, mgenc, msg):
        self._emit2(mgenc, BC.super_send, mgenc.find_literal_index(msg))

    def emitSEND(self, mgenc, msg):
        self._emit2(mgenc, BC.send, mgenc.find_literal_index(msg))

    def emitPUSHCONSTANT(self, mgenc, lit):
        self._emit2(mgenc, BC.push_constant, mgenc.find_literal_index(lit))

    def emitPUSHCONSTANT_index(self, mgenc, lit_index):
        self._emit2(mgenc, BC.push_constant, lit_index)

    def _emit1(self, mgenc, code):
        mgenc.add_bytecode(code)

    def _emit2(self, mgenc, code, idx):
        mgenc.add_bytecode(code)
        mgenc.add_bytecode(idx)

    def _emit3(self, mgenc, code, idx, ctx):
        mgenc.add_bytecode(code)
        mgenc.add_bytecode(idx)
        mgenc.add_bytecode(ctx)
