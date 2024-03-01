from rtruffle.source_section import SourceSection
from rlib.arithmetic import string_to_int, bigint_from_str, ParseStringOverflowError

from som.compiler.lexer import Lexer
from som.compiler.parse_error import ParseError, ParseErrorSymList
from som.compiler.symbol import Symbol

from som.interp_type import is_ast_interpreter
from som.vm.symbols import sym_object, symbol_for, sym_nil
from som.vmobjects.double import Double

if is_ast_interpreter():
    from som.compiler.ast.method_generation_context import MethodGenerationContext
else:
    from som.compiler.bc.method_generation_context import MethodGenerationContext


class ParserBase(object):
    _single_op_syms = [
        Symbol.Not,
        Symbol.And,
        Symbol.Or,
        Symbol.Star,
        Symbol.Div,
        Symbol.Mod,
        Symbol.Plus,
        Symbol.Equal,
        Symbol.More,
        Symbol.Less,
        Symbol.Comma,
        Symbol.At,
        Symbol.Minus,
        Symbol.Per,
    ]

    _binary_op_syms = [
        Symbol.Or,
        Symbol.Comma,
        Symbol.Minus,
        Symbol.Equal,
        Symbol.Not,
        Symbol.And,
        Symbol.Or,
        Symbol.Star,
        Symbol.Div,
        Symbol.Mod,
        Symbol.Plus,
        Symbol.Equal,
        Symbol.More,
        Symbol.Less,
        Symbol.Comma,
        Symbol.At,
        Symbol.Per,
    ]

    _keyword_selector_syms = [Symbol.Keyword, Symbol.KeywordSequence]

    def __init__(self, reader, file_name, universe):
        self.universe = universe
        self._file_name = file_name

        self._lexer = Lexer(reader)
        self._source_reader = reader

        self._sym = Symbol.NONE
        self._text = None
        self._next_sym = Symbol.NONE
        self._get_symbol_from_lexer()
        self._super_send = False

    def _get_source_section(self, coord):
        return SourceSection(
            self._source_reader,
            "method",
            coord,
            self._lexer.get_number_of_characters_read(),
            self._file_name,
        )

    def classdef(self, cgenc):
        cgenc.name = symbol_for(self._text)
        self._expect(Symbol.Identifier)
        self._expect(Symbol.Equal)

        self._superclass(cgenc)

        self._expect(Symbol.NewTerm)
        self._instance_fields(cgenc)

        while (
            self._sym_is_identifier()
            or self._sym == Symbol.Keyword
            or self._sym == Symbol.OperatorSequence
            or self._sym_in(self._binary_op_syms)
        ):
            coord = self._lexer.get_source_coordinate()
            mgenc = MethodGenerationContext(self.universe, cgenc, None)
            mgenc.add_argument("self", self._get_source_section(coord), self)

            cgenc.add_instance_method(mgenc.assemble(self.method(mgenc)))

        if self._accept(Symbol.Separator):
            cgenc.switch_to_class_side()
            self._class_fields(cgenc)

            while (
                self._sym_is_identifier()
                or self._sym == Symbol.Keyword
                or self._sym == Symbol.OperatorSequence
                or self._sym_in(self._binary_op_syms)
            ):
                coord = self._lexer.get_source_coordinate()
                mgenc = MethodGenerationContext(self.universe, cgenc, None)
                mgenc.add_argument("self", self._get_source_section(coord), self)

                cgenc.add_class_method(mgenc.assemble(self.method(mgenc)))

        self._expect(Symbol.EndTerm)

    def _superclass(self, cgenc):
        if self._sym == Symbol.Identifier:
            super_name = symbol_for(self._text)
            self._accept(Symbol.Identifier)
        else:
            super_name = sym_object

        # Load the super class, if it is not nil (break the dependency cycle)
        if super_name is not sym_nil:
            super_class = self.universe.load_class(super_name)
            if not super_class:
                raise ParseError(
                    "Super class %s could not be loaded"
                    % super_name.get_embedded_string(),
                    Symbol.NONE,
                    self,
                )
            cgenc.set_super_class(super_class)

    def _sym_in(self, symbol_list):
        return self._sym in symbol_list

    def _sym_is_identifier(self):
        return self._sym == Symbol.Identifier or self._sym == Symbol.Primitive

    def _accept(self, s):
        if self._sym == s:
            self._get_symbol_from_lexer()
            return True
        return False

    def _accept_one_of(self, symbol_list):
        if self._sym_in(symbol_list):
            self._get_symbol_from_lexer()
            return True
        return False

    def _expect(self, s):
        if self._accept(s):
            return True
        raise ParseError(
            "Unexpected symbol. Expected %(expected)s, but found %(found)s", s, self
        )

    def _expect_one_of(self, symbol_list):
        if self._accept_one_of(symbol_list):
            return True
        raise ParseErrorSymList(
            "Unexpected symbol. Expected one of %(expected)s, but found %(found)s",
            symbol_list,
            self,
        )

    def _instance_fields(self, cgenc):
        if self._accept(Symbol.Or):
            while self._sym_is_identifier():
                var = self._variable()
                cgenc.add_instance_field(symbol_for(var))
            self._expect(Symbol.Or)

    def _class_fields(self, cgenc):
        if self._accept(Symbol.Or):
            while self._sym_is_identifier():
                var = self._variable()
                cgenc.add_class_field(symbol_for(var))
            self._expect(Symbol.Or)

    def _pattern(self, mgenc):
        if self._sym_is_identifier():
            self._unary_pattern(mgenc)
        elif self._sym == Symbol.Keyword:
            self._keyword_pattern(mgenc)
        else:
            self._binary_pattern(mgenc)

    def _unary_pattern(self, mgenc):
        mgenc.signature = self._unary_selector()

    def _binary_pattern(self, mgenc):
        mgenc.signature = self._binary_selector()
        coord = self._lexer.get_source_coordinate()
        mgenc.add_argument(self._argument(), self._get_source_section(coord), self)

    def _keyword_pattern(self, mgenc):
        keyword = self._keyword()
        coord = self._lexer.get_source_coordinate()
        mgenc.add_argument(self._argument(), self._get_source_section(coord), self)

        while self._sym == Symbol.Keyword:
            keyword += self._keyword()
            coord = self._lexer.get_source_coordinate()
            mgenc.add_argument(self._argument(), self._get_source_section(coord), self)

        mgenc.signature = symbol_for(keyword)

    def _unary_selector(self):
        return symbol_for(self._identifier())

    def _binary_selector(self):
        s = self._text

        if self._accept_one_of(self._single_op_syms):
            pass
        elif self._accept(Symbol.OperatorSequence):
            pass
        else:
            self._expect(Symbol.NONE)

        return symbol_for(s)

    def _identifier(self):
        s = self._text
        is_primitive = self._accept(Symbol.Primitive)
        if not is_primitive:
            self._expect(Symbol.Identifier)
        return s

    def _keyword(self):
        s = self._text
        self._expect(Symbol.Keyword)
        return s

    def _argument(self):
        return self._variable()

    def _locals(self, mgenc):
        while self._sym_is_identifier():
            coordinate = self._lexer.get_source_coordinate()
            mgenc.add_local(
                self._variable(), self._get_source_section(coordinate), self
            )

    def _variable(self):
        return self._identifier()

    def _expression(self, mgenc):
        self._peek_for_next_symbol_from_lexer_if_necessary()

        if self._next_sym == Symbol.Assign:
            return self._assignation(mgenc)
        return self._evaluation(mgenc)

    def _assignation(self, _):
        raise Exception("Implemented in subclass")

    def _evaluation(self, _):
        raise Exception("Implemented in subclass")

    def _nested_term(self, mgenc):
        self._expect(Symbol.NewTerm)
        exp = self._expression(mgenc)
        self._expect(Symbol.EndTerm)
        return exp

    def _literal_decimal(self, negate_value):
        if self._sym == Symbol.Integer:
            return self._literal_integer(negate_value)
        if self._sym == Symbol.Double:
            return self._literal_double(negate_value)
        raise ParseError(
            "Could not parse double. " "Expected a number but got '%s'" % self._text,
            Symbol.Double,
            self,
        )

    def _negative_decimal(self):
        self._expect(Symbol.Minus)
        return self._literal_decimal(True)

    def _literal_integer(self, negate_value):
        from som.vmobjects.integer import Integer

        try:
            i = string_to_int(self._text)
            if negate_value:
                i = 0 - i
            result = Integer(i)
        except ParseStringOverflowError:
            from som.vmobjects.biginteger import BigInteger

            bigint = bigint_from_str(self._text)
            if negate_value:
                bigint._set_sign(-1)  # pylint: disable=protected-access
            result = BigInteger(bigint)
        except ValueError:
            raise ParseError(
                "Could not parse integer. "
                "Expected a number but got '%s'" % self._text,
                Symbol.NONE,
                self,
            )
        self._expect(Symbol.Integer)
        return result

    def _literal_double(self, negate_value):
        try:
            value = float(self._text)
            if negate_value:
                value = 0.0 - value
        except ValueError:
            raise ParseError(
                "Could not parse double. "
                "Expected a number but got '%s'" % self._text,
                Symbol.NONE,
                self,
            )
        self._expect(Symbol.Double)
        return Double(value)

    def _selector(self):
        if self._sym == Symbol.OperatorSequence or self._sym_in(self._single_op_syms):
            return self._binary_selector()
        if self._sym == Symbol.Keyword or self._sym == Symbol.KeywordSequence:
            return self._keyword_selector()
        return self._unary_selector()

    def _keyword_selector(self):
        s = self._text
        self._expect_one_of(self._keyword_selector_syms)
        symb = symbol_for(s)
        return symb

    def _string(self):
        s = self._text
        self._expect(Symbol.STString)
        return s

    def _block_pattern(self, mgenc):
        self._block_arguments(mgenc)
        self._expect(Symbol.Or)

    def _block_arguments(self, mgenc):
        self._expect(Symbol.Colon)
        coord = self._lexer.get_source_coordinate()
        mgenc.add_argument(self._argument(), self._get_source_section(coord), self)

        while self._sym == Symbol.Colon:
            self._accept(Symbol.Colon)
            coord = self._lexer.get_source_coordinate()
            mgenc.add_argument(self._argument(), self._get_source_section(coord), self)

    def method(self, mgenc):
        self._pattern(mgenc)
        self._expect(Symbol.Equal)
        if self._sym == Symbol.Primitive:
            mgenc.set_primitive()
            return self._primitive_block()
        return self._method_block(mgenc)

    def _method_block(self, _):
        raise Exception("Implemented in subclass")

    def _block_contents(self, mgenc):
        if self._accept(Symbol.Or):
            self._locals(mgenc)
            self._expect(Symbol.Or)

        mgenc.complete_lexical_scope()

        return self._block_body(mgenc, False)

    def _block_body(self, _a, _b):
        raise Exception("Implemented in subclass")

    def _primitive_block(self):
        self._expect(Symbol.Primitive)

    def _get_symbol_from_lexer(self):
        self._sym = self._lexer.get_sym()
        self._text = self._lexer.text

    def _peek_for_next_symbol_from_lexer(self):
        self._next_sym = self._lexer.peek()

    def _peek_for_next_symbol_from_lexer_if_necessary(self):
        if not self._lexer.peek_done:
            self._peek_for_next_symbol_from_lexer()

    def _nested_block_signature(self, mgenc):
        coord = self._lexer.get_source_coordinate()
        self._expect(Symbol.NewBlock)

        mgenc.add_argument("$blockSelf", self._get_source_section(coord), self)

        if self._sym == Symbol.Colon:
            self._block_pattern(mgenc)

        mgenc.set_block_signature(
            self._lexer.line_number, self._lexer.get_current_column()
        )
