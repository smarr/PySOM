from rtruffle.source_section import SourceSection

from .method_generation_context import MethodGenerationContext
from ..parse_error import ParseError
from ..parser import ParserBase

from ...interpreter.ast.nodes.block_node import BlockNode, BlockNodeWithContext
from ...interpreter.ast.nodes.global_read_node import UninitializedGlobalReadNode
from ...interpreter.ast.nodes.literal_node import LiteralNode
from ...interpreter.ast.nodes.message.uninitialized_node import UninitializedMessageNode
from ...interpreter.ast.nodes.return_non_local_node import ReturnNonLocalNode
from ...interpreter.ast.nodes.sequence_node import SequenceNode

from ..symbol import Symbol
from ...vmobjects.string import String


class Parser(ParserBase):

    def __init__(self, reader, file_name, universe):
        ParserBase.__init__(self, reader, file_name, universe)
        self._source_reader = reader

    def _get_source_section(self, coord):
        return SourceSection(
            self._source_reader, "method", coord,
            self._lexer.get_number_of_characters_read(),
            self._file_name)

    def _assign_source(self, node, coord):
        node.assign_source_section(self._get_source_section(coord))
        return node

    def _method_block(self, mgenc):
        self._expect(Symbol.NewTerm)
        method_body = self._block_contents(mgenc)
        self._expect(Symbol.EndTerm)
        return method_body

    def _block_body(self, mgenc, _seen_period):
        coordinate = self._lexer.get_source_coordinate()
        expressions = []

        while True:
            if self._accept(Symbol.Exit):
                expressions.append(self._result(mgenc))
                return self._create_sequence_node(coordinate, expressions)
            elif self._sym == Symbol.EndBlock:
                return self._create_sequence_node(coordinate, expressions)
            elif self._sym == Symbol.EndTerm:
                # the end of the method has been found (EndTerm) - make it
                # implicitly return "self"
                self_exp = self._variable_read(mgenc, "self")
                self_coord = self._lexer.get_source_coordinate()
                self._assign_source(self_exp, self_coord)
                expressions.append(self_exp)
                return self._create_sequence_node(coordinate, expressions)

            expressions.append(self._expression(mgenc))
            self._accept(Symbol.Period)

    def _create_sequence_node(self, coordinate, expressions):
        if not expressions:
            nil_exp = UninitializedGlobalReadNode(
                self._universe.symbol_for("nil"), self._universe)
            return self._assign_source(nil_exp, coordinate)
        if len(expressions) == 1:
            return expressions[0]

        return SequenceNode(expressions[:], self._get_source_section(coordinate))

    def _result(self, mgenc):
        exp   = self._expression(mgenc)
        coord = self._lexer.get_source_coordinate()

        self._accept(Symbol.Period)

        if mgenc.is_block_method():
            node = ReturnNonLocalNode(mgenc.get_outer_self_context_level(),
                                      exp, self._universe)
            mgenc.make_catch_non_local_return()
            return self._assign_source(node, coord)
        else:
            return exp

    def _assignation(self, mgenc):
        return self._assignments(mgenc)

    def _assignments(self, mgenc):
        coord = self._lexer.get_source_coordinate()

        if not self._sym_is_identifier():
            raise ParseError("Assignments should always target variables or"
                             " fields, but found instead a %(found)s",
                             Symbol.Identifier, self)

        variable = self._assignment()
        self._peek_for_next_symbol_from_lexer()

        if self._next_sym == Symbol.Assign:
            value = self._assignments(mgenc)
        else:
            value = self._evaluation(mgenc)

        exp = self._variable_write(mgenc, variable, value)
        return self._assign_source(exp, coord)

    def _assignment(self):
        var_name = self._variable()
        self._expect(Symbol.Assign)
        return var_name

    def _evaluation(self, mgenc):
        exp = self._primary(mgenc)

        if (self._sym_is_identifier()            or
            self._sym == Symbol.Keyword          or
            self._sym == Symbol.OperatorSequence or
            self._sym_in(self._binary_op_syms)):
            exp = self._messages(mgenc, exp)
        return exp

    def _primary(self, mgenc):
        if self._sym_is_identifier():
            coordinate = self._lexer.get_source_coordinate()
            var_name = self._variable()
            var_read = self._variable_read(mgenc, var_name)
            return self._assign_source(var_read, coordinate)

        if self._sym == Symbol.NewTerm:
            return self._nested_term(mgenc)

        if self._sym == Symbol.NewBlock:
            coordinate = self._lexer.get_source_coordinate()
            bgenc = MethodGenerationContext(self._universe)
            bgenc.set_is_block_method(True)
            bgenc.set_holder(mgenc.get_holder())
            bgenc.set_outer(mgenc)

            block_body   = self._nested_block(bgenc)
            block_method = bgenc.assemble(block_body)
            mgenc.add_embedded_block_method(block_method)

            if bgenc.requires_context():
                result = BlockNodeWithContext(block_method, self._universe)
            else:
                result = BlockNode(block_method, self._universe)
            return self._assign_source(result, coordinate)

        return self._literal()

    def _messages(self, mgenc, receiver):
        msg = receiver

        while self._sym_is_identifier():
            msg = self._unary_message(msg)

        while (self._sym == Symbol.OperatorSequence or
               self._sym_in(self._binary_op_syms)):
            msg = self._binary_message(mgenc, msg)

        if self._sym == Symbol.Keyword:
            msg = self._keyword_message(mgenc, msg)

        return msg

    def _unary_message(self, receiver):
        coord = self._lexer.get_source_coordinate()
        selector = self._unary_selector()
        msg = UninitializedMessageNode(selector, self._universe, receiver, [])
        return self._assign_source(msg, coord)

    def _binary_message(self, mgenc, receiver):
        coord    = self._lexer.get_source_coordinate()
        selector = self._binary_selector()
        operand  = self._binary_operand(mgenc)

        msg = UninitializedMessageNode(selector, self._universe, receiver,
                                       [operand])
        return self._assign_source(msg, coord)

    def _binary_operand(self, mgenc):
        operand = self._primary(mgenc)

        while self._sym_is_identifier():
            operand = self._unary_message(operand)
        return operand

    def _keyword_message(self, mgenc, receiver):
        coord = self._lexer.get_source_coordinate()
        arguments = []
        keyword   = []

        while self._sym == Symbol.Keyword:
            keyword.append(self._keyword())
            arguments.append(self._formula(mgenc))

        selector = self._universe.symbol_for("".join(keyword))
        msg = UninitializedMessageNode(selector, self._universe, receiver,
                                       arguments[:])
        return self._assign_source(msg, coord)

    def _formula(self, mgenc):
        operand = self._binary_operand(mgenc)

        while (self._sym == Symbol.OperatorSequence or
               self._sym_in(self._binary_op_syms)):
            operand = self._binary_message(mgenc, operand)
        return operand

    def _literal(self):
        coord = self._lexer.get_source_coordinate()
        val = self._get_object_for_current_literal()

        lit = LiteralNode(val)
        self._assign_source(lit, coord)
        return lit

    def _get_object_for_current_literal(self):
        if self._sym == Symbol.Pound:
            self._peek_for_next_symbol_from_lexer_if_necessary()

            if self._next_sym == Symbol.NewTerm:
                return self._literal_array()
            else:
                return self._literal_symbol()
        elif self._sym == Symbol.STString:
            return self._literal_string()
        else:
            return self._literal_number()

    def _literal_number(self):
        if self._sym == Symbol.Minus:
            return self._negative_decimal()
        else:
            return self._literal_decimal(False)

    def _literal_symbol(self):
        self._expect(Symbol.Pound)
        if self._sym == Symbol.STString:
            s = self._string()
            return self._universe.symbol_for(s)
        else:
            return self._selector()

    def _literal_string(self):
        s = self._string()
        return String(s)

    def _literal_array(self):
        literals = []
        self._expect(Symbol.Pound)
        self._expect(Symbol.NewTerm)
        while self._sym != Symbol.EndTerm:
            literals.append(self._get_object_for_current_literal())
        self._expect(Symbol.EndTerm)
        return self._universe.new_array_from_list(literals[:])

    def _nested_block(self, mgenc):
        self._nested_block_signature(mgenc)
        expressions = self._block_contents(mgenc)
        self._expect(Symbol.EndBlock)
        return expressions

    def _variable_read(self, mgenc, variable_name):
        # 'super' needs to be handled separately
        if variable_name == "super":
            variable = mgenc.get_variable("self")
            return variable.get_super_read_node(
                mgenc.get_outer_self_context_level(),
                mgenc.get_holder().get_name(),
                mgenc.get_holder().is_class_side(),
                self._universe)

        # first lookup in local variables, or method arguments
        variable = mgenc.get_variable(variable_name)
        if variable:
            return variable.get_read_node(
                mgenc.get_context_level(variable_name))

        # otherwise, it might be an object field
        var_symbol = self._universe.symbol_for(variable_name)
        field_read = mgenc.get_object_field_read(var_symbol)
        if field_read:
            return field_read

        # nope, so, it is a global?
        return mgenc.get_global_read(var_symbol)

    def _variable_write(self, mgenc, variable_name, exp):
        if variable_name == "self":
            raise ParseError(
                "It is not possible to write to `self`, it is a pseudo variable", Symbol.NONE, self)
        if variable_name == "super":
            raise ParseError(
                "It is not possible to write to `super`, it is a pseudo variable", Symbol.NONE, self)

        variable = mgenc.get_variable(variable_name)
        if variable:
            return variable.get_write_node(
                mgenc.get_context_level(variable_name), exp)

        field_name = self._universe.symbol_for(variable_name)
        field_write = mgenc.get_object_field_write(field_name, exp)
        if field_write:
            return field_write
        else:
            raise RuntimeError("Neither a variable nor a field found in current"
                               " scope that is named " + variable_name + ".")


