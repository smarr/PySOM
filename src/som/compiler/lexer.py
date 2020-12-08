from rtruffle.source_section import SourceCoordinate
from .symbol import Symbol


class Lexer(object):

    _SEPARATOR = "----"
    _PRIMITIVE = "primitive"

    def __init__(self, input_file):
        self._line_number = 0
        self._chars_read  = 0 # all characters read, excluding the current line
        self._infile      = input_file
        self._sym         = Symbol.NONE
        self._symc        = '\0'
        self._text        = ""
        self._peek_done   = False
        self._next_sym    = Symbol.NONE
        self._next_symc   = '\0'
        self._next_text   = ""
        self._buf         = ""
        self._bufp        = 0

    def get_source_coordinate(self):
        return SourceCoordinate(self._line_number,
                                self._bufp + 1,
                                self._chars_read + self._bufp)

    def _lex_number(self):
        self._sym = Symbol.Integer
        self._symc = '\0'
        self._text = ''

        saw_decimal_mark = False

        while self._current_char().isdigit():
            self._text += self._current_char()
            self._bufp += 1

            if (not saw_decimal_mark and '.' == self._current_char() and
                    self._bufchar(self._bufp + 1).isdigit()):
                self._sym = Symbol.Double
                saw_decimal_mark = True
                self._text += self._current_char()
                self._bufp += 1

    def _lex_operator(self):
        if self._is_operator(self._bufchar(self._bufp + 1)):
            self._sym = Symbol.OperatorSequence
            self._symc = '\0'
            self._text = ""
            while self._is_operator(self._current_char()):
                self._text += self._current_char()
                self._bufp += 1
        elif self._current_char() == '~':
            self._match(Symbol.Not)
        elif self._current_char() == '&':
            self._match(Symbol.And)
        elif self._current_char() == '|':
            self._match(Symbol.Or)
        elif self._current_char() == '*':
            self._match(Symbol.Star)
        elif self._current_char() == '/':
            self._match(Symbol.Div)
        elif self._current_char() == '\\':
            self._match(Symbol.Mod)
        elif self._current_char() == '+':
            self._match(Symbol.Plus)
        elif self._current_char() == '=':
            self._match(Symbol.Equal)
        elif self._current_char() == '>':
            self._match(Symbol.More)
        elif self._current_char() == '<':
            self._match(Symbol.Less)
        elif self._current_char() == ',':
            self._match(Symbol.Comma)
        elif self._current_char() == '@':
            self._match(Symbol.At)
        elif self._current_char() == '%':
            self._match(Symbol.Per)
        elif self._current_char() == '-':
            self._match(Symbol.Minus)

    def _lex_escape_char(self):
        if self._end_of_buffer():
            raise Exception("Invalid escape sequence")

        if self._current_char() == "t":
            self._text += "\t"
        elif self._current_char() == "b":
            self._text += "\b"
        elif self._current_char() == "n":
            self._text += "\n"
        elif self._current_char() == "r":
            self._text += "\r"
        elif self._current_char() == "f":
            self._text += "\f"
        elif self._current_char() == "0":
            self._text += "\0"
        elif self._current_char() == "'":
            self._text += "'"
        elif self._current_char() == "\\":
            self._text += "\\"

        self._bufp += 1

    def _lex_string_char(self):
        if self._current_char() == '\\':
            self._bufp += 1
            self._lex_escape_char()
        else:
            self._text += self._current_char()
            self._bufp += 1

        while self._end_of_buffer():
            if self._fill_buffer() == -1:
                return

    def _lex_string(self):
        self._sym = Symbol.STString
        self._symc = '\0'
        self._bufp += 1
        self._text = ""

        while self._current_char() != '\'':
            self._lex_string_char()

        self._bufp += 1

    def get_sym(self):
        if self._peek_done:
            self._peek_done = False
            self._sym  = self._next_sym
            self._symc = self._next_symc
            self._text = self._next_text
            return self._sym

        while True:
            if not self._has_more_input():
                self._sym = Symbol.NONE
                self._symc = '\0'
                self._text = self._symc
                return self._sym
            self._skip_white_space()
            self._skip_comment()

            if (not self._end_of_buffer()          and
                    not self._current_char().isspace() and
                    not self._current_char() == '"'):
                break

        if self._current_char() == '\'':
            self._lex_string()
        elif self._current_char() == '[':
            self._match(Symbol.NewBlock)
        elif self._current_char() == ']':
            self._match(Symbol.EndBlock)
        elif self._current_char() == ':':
            if self._bufchar(self._bufp + 1) == '=':
                self._bufp += 2
                self._sym = Symbol.Assign
                self._symc = '\0'
                self._text = ":="
            else:
                self._bufp += 1
                self._sym = Symbol.Colon
                self._symc = ':'
                self._text = ":"

        elif self._current_char() == '(':
            self._match(Symbol.NewTerm)
        elif self._current_char() == ')':
            self._match(Symbol.EndTerm)
        elif self._current_char() == '#':
            self._match(Symbol.Pound)
        elif self._current_char() == '^':
            self._match(Symbol.Exit)
        elif self._current_char() == '.':
            self._match(Symbol.Period)
        elif self._current_char() == '-':
            if self._buf[self._bufp:].startswith(self._SEPARATOR):
                self._text = ""
                while self._current_char() == '-':
                    self._text += self._current_char()
                    self._bufp += 1
                self._sym = Symbol.Separator
            else:
                self._lex_operator()

        elif self._is_operator(self._current_char()):
            self._lex_operator()

        elif self._next_word_in_buffer_is(self._PRIMITIVE):
            self._bufp += len(self._PRIMITIVE)
            self._sym  = Symbol.Primitive
            self._symc = '\0'
            self._text = self._PRIMITIVE
        elif self._current_char().isalpha():
            self._symc = '\0'
            self._text = ""
            while self._current_char().isalnum() or self._current_char() == '_':
                self._text += self._current_char()
                self._bufp += 1
            self._sym = Symbol.Identifier
            if self._current_char() == ':':
                self._sym = Symbol.Keyword
                self._bufp += 1
                self._text += ':'
                if self._current_char().isalpha():
                    self._sym = Symbol.KeywordSequence
                    while (self._current_char().isalpha() or
                           self._current_char() == ':'):
                        self._text += self._current_char()
                        self._bufp += 1
        elif self._current_char().isdigit():
            self._lex_number()
        else:
            self._sym  = Symbol.NONE
            self._symc = self._current_char()
            self._text = self._symc

        return self._sym

    def _next_word_in_buffer_is(self, text):
        if not self._buf[self._bufp:].startswith(text):
            return False
        char_after_text = self._bufchar(self._bufp + len(text))
        return not char_after_text.isalnum()

    def get_peek_done(self):
        return self._peek_done

    def peek(self):
        save_sym  = self._sym
        save_symc = self._symc
        save_text = self._text

        if self._peek_done:
            raise ValueError("SOM lexer: cannot peek twice!")

        self.get_sym()
        self._next_sym  = self._sym
        self._next_symc = self._symc
        self._next_text = self._text

        self._sym  = save_sym
        self._symc = save_symc
        self._text = save_text

        self._peek_done = True

        return self._next_sym

    def get_text(self):
        return self._text

    def next_text(self):
        return self._next_text

    def get_raw_buffer(self):
        return self._buf

    def get_current_line_number(self):
        return self._line_number

    def get_current_column(self):
        return self._bufp + 1

    # All characters read and processed, including current line
    def get_number_of_characters_read(self):
        return self._chars_read + self._bufp

    def _fill_buffer(self):
        try:
            self._chars_read += len(self._buf)
            self._buf = self._infile.readline()
            if self._buf == '':
                return -1
            self._line_number += 1
            self._bufp = 0
            return len(self._buf)
        except IOError as ioe:
            raise ValueError("Error reading from input: " + str(ioe))

    def _has_more_input(self):
        while self._end_of_buffer():
            if self._fill_buffer() == -1:
                return False
        return True

    def _skip_white_space(self):
        while self._current_char().isspace():
            self._bufp += 1
            while self._end_of_buffer():
                if self._fill_buffer() == -1:
                    return

    def _skip_comment(self):
        if self._current_char() == '"':
            while True:
                self._bufp += 1
                while self._end_of_buffer():
                    if self._fill_buffer() == -1:
                        return
                if self._current_char() == '"':
                    break
            self._bufp += 1

    def _current_char(self):
        return self._bufchar(self._bufp)

    def _end_of_buffer(self):
        return self._bufp >= len(self._buf)

    @staticmethod
    def _is_operator(c):
        return (c == '~'  or c == '&' or c == '|' or c == '*' or c == '/' or
                c == '\\' or c == '+' or c == '=' or c == '>' or c == '<' or
                c == ','  or c == '@' or c == '%' or c == '-')

    def _match(self, s):
        self._sym  = s
        self._symc = self._current_char()
        self._text = self._symc
        self._bufp += 1

    def _bufchar(self, p):
        return '\0' if p >= len(self._buf) else self._buf[p]
