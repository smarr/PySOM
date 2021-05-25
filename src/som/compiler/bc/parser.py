from .bytecode_generator import BytecodeGenerator
from .method_generation_context import MethodGenerationContext
from ..parser import ParserBase
from ..symbol import Symbol
from ...vmobjects.integer import Integer
from ...vmobjects.string import String


class Parser(ParserBase):

    def __init__(self, reader, file_name, universe):
        ParserBase.__init__(self, reader, file_name, universe)
        self._bc_gen = BytecodeGenerator()

    def _method_block(self, mgenc):
        self._expect(Symbol.NewTerm)
        self._block_contents(mgenc)

        # if no return has been generated so far, we can be sure there was no .
        # terminating the last expression, so the last expression's value must
        # be popped off the stack and a ^self be generated
        if not mgenc.is_finished():
            self._bc_gen.emitPOP(mgenc)
            self._bc_gen.emitPUSHARGUMENT(mgenc, 0, 0)
            self._bc_gen.emitRETURNLOCAL(mgenc)
            mgenc.set_finished()

        self._expect(Symbol.EndTerm)
        return None

    def _block_body(self, mgenc, seen_period):
        if self._accept(Symbol.Exit):
            self._result(mgenc)
        elif self._sym == Symbol.EndBlock:
            if seen_period:
                # a POP has been generated which must be elided (blocks always
                # return the value of the last expression, regardless of
                # whether it was terminated with a . or not)
                mgenc.remove_last_bytecode()

            # if this block is empty, we need to return nil
            if mgenc.is_block_method() and not mgenc.has_bytecode():
                nil_sym = self._universe.symbol_for("nil")
                mgenc.add_literal_if_absent(nil_sym)
                self._bc_gen.emitPUSHGLOBAL(mgenc, nil_sym)

            self._bc_gen.emitRETURNLOCAL(mgenc)
            mgenc.set_finished()
        elif self._sym == Symbol.EndTerm:
            # it does not matter whether a period has been seen, as the end of
            # the method has been found (EndTerm) - so it is safe to emit a
            # "return self"
            self._bc_gen.emitPUSHARGUMENT(mgenc, 0, 0)
            self._bc_gen.emitRETURNLOCAL(mgenc)
            mgenc.set_finished()
        else:
            self._expression(mgenc)
            if self._accept(Symbol.Period):
                self._bc_gen.emitPOP(mgenc)
                self._block_body(mgenc, True)

    def _result(self, mgenc):
        self._expression(mgenc)
        self._accept(Symbol.Period)

        if mgenc.is_block_method():
            self._bc_gen.emitRETURNNONLOCAL(mgenc)
        else:
            self._bc_gen.emitRETURNLOCAL(mgenc)

        mgenc.set_finished()

    def _assignation(self, mgenc):
        l = []

        self._assignments(mgenc, l)
        self._evaluation(mgenc)

        for _assignment in l:
            self._bc_gen.emitDUP(mgenc)

        for assignment in l:
            self._gen_pop_variable(mgenc, assignment)
        return None

    def _assignments(self, mgenc, l):
        if self._sym_is_identifier():
            l.append(self._assignment(mgenc))
            self._peek_for_next_symbol_from_lexer()
            if self._next_sym == Symbol.Assign:
                self._assignments(mgenc, l)

    def _assignment(self, mgenc):
        v   = self._variable()
        var = self._universe.symbol_for(v)
        mgenc.add_literal_if_absent(var)

        self._expect(Symbol.Assign)
        return v

    def _evaluation(self, mgenc):
        is_super_send = self._primary(mgenc)

        if (self._sym_is_identifier()            or
            self._sym == Symbol.Keyword          or
            self._sym == Symbol.OperatorSequence or
            self._sym_in(self._binary_op_syms)):
            self._messages(mgenc, is_super_send)
        return None

    def _primary(self, mgenc):
        is_super_send = False

        if self._sym_is_identifier():
            v = self._variable()
            if v == "super":
                is_super_send = True
                # sends to super push self as the receiver
                v = "self"
            self._gen_push_variable(mgenc, v)

        elif self._sym == Symbol.NewTerm:
            self._nested_term(mgenc)
        elif self._sym == Symbol.NewBlock:
            bgenc = MethodGenerationContext(self._universe)
            bgenc.set_is_block_method(True)
            bgenc.set_holder(mgenc.get_holder())
            bgenc.set_outer(mgenc)

            self._nested_block(bgenc)

            block_method = bgenc.assemble(None)
            mgenc.add_literal(block_method)
            self._bc_gen.emitPUSHBLOCK(mgenc, block_method)
        else:
            self._literal(mgenc)

        return is_super_send

    def _messages(self, mgenc, is_super_send):
        if self._sym_is_identifier():
            while self._sym_is_identifier():
                # only the first message in a sequence can be a super send
                self._unary_message(mgenc, is_super_send)
                is_super_send = False

            while (self._sym == Symbol.OperatorSequence or
                   self._sym_in(self._binary_op_syms)):
                self._binary_message(mgenc, False)

            if self._sym == Symbol.Keyword:
                self._keyword_message(mgenc, False)

        elif (self._sym == Symbol.OperatorSequence or
              self._sym_in(self._binary_op_syms)):
            while (self._sym == Symbol.OperatorSequence or
                   self._sym_in(self._binary_op_syms)):
                # only the first message in a sequence can be a super send
                self._binary_message(mgenc, is_super_send)
                is_super_send = False

            if self._sym == Symbol.Keyword:
                self._keyword_message(mgenc, False)

        else:
            self._keyword_message(mgenc, is_super_send)

    def _unary_message(self, mgenc, is_super_send):
        msg = self._unary_selector()
        mgenc.add_literal_if_absent(msg)

        if is_super_send:
            self._bc_gen.emitSUPERSEND(mgenc, msg)
        else:
            self._bc_gen.emitSEND(mgenc, msg)

    @staticmethod
    def _is_quick_send(msg):
        m = msg.get_embedded_string()
        return m == "+" or m == "-" or m == "*"

    def _binary_message(self, mgenc, is_super_send):
        msg = self._binary_selector()
        mgenc.add_literal_if_absent(msg)

        self._binary_operand(mgenc)

        if is_super_send:
            self._bc_gen.emitSUPERSEND(mgenc, msg)
        elif self._is_quick_send(msg):
            self._bc_gen.emitQUICKSEND(mgenc, msg)
        else:
            self._bc_gen.emitSEND(mgenc, msg)

    def _binary_operand(self, mgenc):
        is_super_send = self._primary(mgenc)

        while self._sym_is_identifier():
            self._unary_message(mgenc, is_super_send)
            is_super_send = False

        return is_super_send

    def _keyword_message(self, mgenc, is_super_send):
        kw = self._keyword()
        self._formula(mgenc)

        while self._sym == Symbol.Keyword:
            kw += self._keyword()
            self._formula(mgenc)

        msg = self._universe.symbol_for(kw)

        mgenc.add_literal_if_absent(msg)

        if is_super_send:
            self._bc_gen.emitSUPERSEND(mgenc, msg)
        else:
            self._bc_gen.emitSEND(mgenc, msg)

    def _formula(self, mgenc):
        is_super_send = self._binary_operand(mgenc)

        # only the first message in a sequence can be a super send
        if self._sym == Symbol.OperatorSequence or self._sym_in(self._binary_op_syms):
            self._binary_message(mgenc, is_super_send)

        while self._sym == Symbol.OperatorSequence or self._sym_in(self._binary_op_syms):
            self._binary_message(mgenc, False)

    def _literal(self, mgenc):
        if self._sym == Symbol.Pound:
            self._peek_for_next_symbol_from_lexer_if_necessary()

            if self._next_sym == Symbol.NewTerm:
                self._literal_array(mgenc)
            else:
                self._literal_symbol(mgenc)
        elif self._sym == Symbol.STString:
            self._literal_string(mgenc)
        else:
            self._literal_number(mgenc)

    def _literal_number(self, mgenc):
        if self._sym == Symbol.Minus:
            lit = self._negative_decimal()
        else:
            lit = self._literal_decimal(False)

        mgenc.add_literal_if_absent(lit)
        self._bc_gen.emitPUSHCONSTANT(mgenc, lit)

    def _literal_symbol(self, mgenc):
        self._expect(Symbol.Pound)
        if self._sym == Symbol.STString:
            s    = self._string()
            symb = self._universe.symbol_for(s)
        else:
            symb = self._selector()

        mgenc.add_literal_if_absent(symb)
        self._bc_gen.emitPUSHCONSTANT(mgenc, symb)

    def _literal_string(self, mgenc):
        s = self._string()

        string = String(s)
        mgenc.add_literal_if_absent(string)

        self._bc_gen.emitPUSHCONSTANT(mgenc, string)

    def _literal_array(self, mgenc):
        self._expect(Symbol.Pound)
        self._expect(Symbol.NewTerm)

        array_class_name = self._universe.symbol_for("Array")
        array_size_placeholder = self._universe.symbol_for("ArraySizeLiteralPlaceholder")
        new_message = self._universe.symbol_for("new:")
        at_put_message = self._universe.symbol_for("at:put:")

        mgenc.add_literal_if_absent(array_class_name)
        mgenc.add_literal_if_absent(new_message)
        mgenc.add_literal_if_absent(at_put_message)

        array_size_literal_idx = mgenc.add_literal(array_size_placeholder)

        # create empty array
        self._bc_gen.emitPUSHGLOBAL(mgenc, array_class_name)
        self._bc_gen.emitPUSHCONSTANT_index(mgenc, array_size_literal_idx)
        self._bc_gen.emitSEND(mgenc, new_message)

        i = 1

        while self._sym != Symbol.EndTerm:
            push_idx = Integer(i)
            mgenc.add_literal_if_absent(push_idx)
            self._bc_gen.emitPUSHCONSTANT(mgenc, push_idx)

            self._literal(mgenc)
            self._bc_gen.emitSEND(mgenc, at_put_message)
            i += 1

        mgenc.update_literal(
            array_size_placeholder, array_size_literal_idx, Integer(i - 1))
        self._expect(Symbol.EndTerm)

    def _nested_block(self, mgenc):
        self._nested_block_signature(mgenc)
        self._block_contents(mgenc)

        # if no return has been generated, we can be sure that the last
        # expression in the block was not terminated by ., and can generate
        # a return
        if not mgenc.is_finished():
            if not mgenc.has_bytecode():
                nil_sym = self._universe.symbol_for("nil")
                mgenc.add_literal_if_absent(nil_sym)
                self._bc_gen.emitPUSHGLOBAL(mgenc, nil_sym)
            self._bc_gen.emitRETURNLOCAL(mgenc)
            mgenc.set_finished()

        self._expect(Symbol.EndBlock)

    def _gen_push_variable(self, mgenc, var):
        # The purpose of this function is to find out whether the variable to be
        # pushed on the stack is a local variable, argument, or object field.
        # This is done by examining all available lexical contexts, starting with
        # the innermost (i.e., the one represented by mgenc).

        # triplet: index, context, isArgument
        triplet = [0, 0, False]

        if mgenc.find_var(var, triplet):
            if triplet[2]:
                self._bc_gen.emitPUSHARGUMENT(mgenc, triplet[0], triplet[1])
            else:
                self._bc_gen.emitPUSHLOCAL(mgenc, triplet[0], triplet[1])
        else:
            identifier = self._universe.symbol_for(var)
            if mgenc.has_field(identifier):
                field_name = identifier
                mgenc.add_literal_if_absent(field_name)
                self._bc_gen.emitPUSHFIELD(mgenc, field_name)
            else:
                globe = identifier
                mgenc.add_literal_if_absent(globe)
                self._bc_gen.emitPUSHGLOBAL(mgenc, globe)

    def _gen_pop_variable(self, mgenc, var):
        # The purpose of this function is to find out whether the variable to be
        # popped off the stack is a local variable, argument, or object field.
        # This is done by examining all available lexical contexts, starting with
        # the innermost (i.e., the one represented by mgenc).

        # triplet: index, context, isArgument
        triplet = [0, 0, False]

        if mgenc.find_var(var, triplet):
            if triplet[2]:
                self._bc_gen.emitPOPARGUMENT(mgenc, triplet[0], triplet[1])
            else:
                self._bc_gen.emitPOPLOCAL(mgenc, triplet[0], triplet[1])
        else:
            self._bc_gen.emitPOPFIELD(mgenc, self._universe.symbol_for(var))
