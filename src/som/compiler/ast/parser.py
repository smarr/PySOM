from rtruffle.source_section import SourceSection

from som.compiler.ast.method_generation_context import MethodGenerationContext
from som.compiler.parse_error import ParseError
from som.compiler.parser import ParserBase
from som.compiler.symbol import Symbol

from som.interpreter.ast.nodes.block_node import BlockNode, BlockNodeWithContext
from som.interpreter.ast.nodes.global_read_node import create_global_node
from som.interpreter.ast.nodes.literal_node import LiteralNode
from som.interpreter.ast.nodes.message.super_node import (
    UnarySuper,
    BinarySuper,
    TernarySuper,
    NArySuper,
)
from som.interpreter.ast.nodes.message.uninitialized_node import (
    UninitializedMessageNode,
)
from som.interpreter.ast.nodes.return_non_local_node import ReturnNonLocalNode
from som.interpreter.ast.nodes.sequence_node import SequenceNode

from som.vmobjects.array import Array
from som.vmobjects.string import String


class Parser(ParserBase):
    def __init__(self, reader, file_name, universe):
        ParserBase.__init__(self, reader, file_name, universe)
        self._source_reader = reader

    def _get_source_section(self, coord):
        return SourceSection(
            self._source_reader,
            "method",
            coord,
            self._lexer.get_number_of_characters_read(),
            self._file_name,
        )

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
            if self._sym == Symbol.EndBlock:
                return self._create_sequence_node(coordinate, expressions)
            if self._sym == Symbol.EndTerm:
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
            nil_exp = create_global_node(
                self.universe.sym_nil,
                self.universe,
                None,
                self._get_source_section(coordinate),
            )
            return nil_exp
        if len(expressions) == 1:
            return expressions[0]

        return SequenceNode(expressions[:], self._get_source_section(coordinate))

    def _result(self, mgenc):
        exp = self._expression(mgenc)
        coord = self._lexer.get_source_coordinate()

        self._accept(Symbol.Period)

        if mgenc.is_block_method:
            node = ReturnNonLocalNode(
                mgenc.get_outer_self_context_level(), exp, self.universe
            )
            mgenc.make_catch_non_local_return()
            return self._assign_source(node, coord)
        return exp

    def _assignation(self, mgenc):
        return self._assignments(mgenc)

    def _assignments(self, mgenc):
        coord = self._lexer.get_source_coordinate()

        if not self._sym_is_identifier():
            raise ParseError(
                "Assignments should always target variables or"
                " fields, but found instead a %(found)s",
                Symbol.Identifier,
                self,
            )

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

        if (
            self._sym_is_identifier()
            or self._sym == Symbol.Keyword
            or self._sym == Symbol.OperatorSequence
            or self._sym_in(self._binary_op_syms)
        ):
            exp = self._messages(mgenc, exp)

        self._super_send = False
        return exp

    def _primary(self, mgenc):
        if self._sym_is_identifier():
            coordinate = self._lexer.get_source_coordinate()
            var_name = self._variable()
            if var_name == "super":
                self._super_send = True
                # sends to super push self as the receiver
                var_name = "self"
            var_read = self._variable_read(mgenc, var_name)
            return self._assign_source(var_read, coordinate)

        if self._sym == Symbol.NewTerm:
            return self._nested_term(mgenc)

        if self._sym == Symbol.NewBlock:
            coordinate = self._lexer.get_source_coordinate()
            bgenc = MethodGenerationContext(self.universe, mgenc)
            bgenc.holder = mgenc.holder

            block_body = self.nested_block(bgenc)
            block_method = bgenc.assemble(block_body)
            mgenc.add_embedded_block_method(block_method)

            if bgenc.requires_context():
                result = BlockNodeWithContext(block_method, self.universe)
            else:
                result = BlockNode(block_method, self.universe)
            return self._assign_source(result, coordinate)

        return self._literal()

    def _messages(self, mgenc, receiver):
        msg = receiver

        while self._sym_is_identifier():
            msg = self._unary_message(mgenc, msg)

        while self._sym == Symbol.OperatorSequence or self._sym_in(
            self._binary_op_syms
        ):
            msg = self._binary_message(mgenc, msg)

        if self._sym == Symbol.Keyword:
            msg = self._keyword_message(mgenc, msg)

        return msg

    def _unary_message(self, mgenc, receiver):
        is_super_send = self._super_send
        self._super_send = False

        coord = self._lexer.get_source_coordinate()
        selector = self._unary_selector()

        if is_super_send:
            msg = UnarySuper(selector, receiver, mgenc.holder.get_super_class())
        else:
            msg = UninitializedMessageNode(selector, self.universe, receiver, [])
        return self._assign_source(msg, coord)

    def _binary_message(self, mgenc, receiver):
        is_super_send = self._super_send
        self._super_send = False

        coord = self._lexer.get_source_coordinate()
        selector = self._binary_selector()
        arg_expr = self._binary_operand(mgenc)

        if is_super_send:
            msg = BinarySuper(
                selector, receiver, arg_expr, mgenc.holder.get_super_class()
            )
        else:
            msg = UninitializedMessageNode(
                selector, self.universe, receiver, [arg_expr]
            )
        return self._assign_source(msg, coord)

    def _binary_operand(self, mgenc):
        operand = self._primary(mgenc)

        while self._sym_is_identifier():
            operand = self._unary_message(mgenc, operand)

        return operand

    def _keyword_message(self, mgenc, receiver):
        is_super_send = self._super_send

        coord = self._lexer.get_source_coordinate()
        arguments = []
        keyword = []

        while self._sym == Symbol.Keyword:
            keyword.append(self._keyword())
            arguments.append(self._formula(mgenc))

        selector = self.universe.symbol_for("".join(keyword))

        if is_super_send:
            num_args = len(arguments) + 1
            if num_args == 2:
                msg = BinarySuper(
                    selector, receiver, arguments[0], mgenc.holder.get_super_class()
                )
            elif num_args == 3:
                msg = TernarySuper(
                    selector,
                    receiver,
                    arguments[0],
                    arguments[1],
                    mgenc.holder.get_super_class(),
                )
            else:
                msg = NArySuper(
                    selector, receiver, arguments[:], mgenc.holder.get_super_class()
                )
        else:
            msg = UninitializedMessageNode(
                selector, self.universe, receiver, arguments[:]
            )
        return self._assign_source(msg, coord)

    def _formula(self, mgenc):
        operand = self._binary_operand(mgenc)

        while self._sym == Symbol.OperatorSequence or self._sym_in(
            self._binary_op_syms
        ):
            operand = self._binary_message(mgenc, operand)

        self._super_send = False
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
            return self._literal_symbol()
        if self._sym == Symbol.STString:
            return self._literal_string()
        return self._literal_number()

    def _literal_number(self):
        if self._sym == Symbol.Minus:
            return self._negative_decimal()
        return self._literal_decimal(False)

    def _literal_symbol(self):
        self._expect(Symbol.Pound)
        if self._sym == Symbol.STString:
            s = self._string()
            return self.universe.symbol_for(s)
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
        return Array.from_values(literals[:])

    def nested_block(self, mgenc):
        self._nested_block_signature(mgenc)
        expressions = self._block_contents(mgenc)
        self._expect(Symbol.EndBlock)
        return expressions

    def _variable_read(self, mgenc, variable_name):
        # first lookup in local variables, or method arguments
        variable = mgenc.get_variable(variable_name)
        if variable:
            return variable.get_read_node(mgenc.get_context_level(variable_name))

        # otherwise, it might be an object field
        var_symbol = self.universe.symbol_for(variable_name)
        field_read = mgenc.get_object_field_read(var_symbol)
        if field_read:
            return field_read

        # nope, so, it is a global?
        return mgenc.get_global_read(var_symbol)

    def _variable_write(self, mgenc, variable_name, exp):
        if variable_name == "self":
            raise ParseError(
                "It is not possible to write to `self`, it is a pseudo variable",
                Symbol.NONE,
                self,
            )
        if variable_name == "super":
            raise ParseError(
                "It is not possible to write to `super`, it is a pseudo variable",
                Symbol.NONE,
                self,
            )

        variable = mgenc.get_variable(variable_name)
        if variable:
            return variable.get_write_node(mgenc.get_context_level(variable_name), exp)

        field_name = self.universe.symbol_for(variable_name)
        field_write = mgenc.get_object_field_write(field_name, exp)
        if field_write:
            return field_write
        raise RuntimeError(
            "Neither a variable nor a field found in current"
            " scope that is named " + variable_name + "."
        )
