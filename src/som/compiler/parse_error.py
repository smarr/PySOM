from som.compiler.symbol import Symbol, symbol_as_str


class ParseError(Exception):
    def __init__(self, message, expected_sym, parser):
        self._message           = message
        self._source_coordinate = parser._lexer.get_source_coordinate()
        self._text              = parser._text
        self._raw_buffer        = parser._lexer.get_raw_buffer()
        self._file_name         = parser._file_name
        self._expected_sym      = expected_sym
        self._found_sym         = parser._sym

    def _is_printable_symbol(self):
        return (self._found_sym == Symbol.Integer or
                self._found_sym == Symbol.Double  or
                self._found_sym >= Symbol.STString)

    def _expected_sym_str(self):
        return symbol_as_str(self._expected_sym)

    def __str__(self):
        msg = "%(file)s:%(line)d:%(column)d: error: " + self._message
        if self._is_printable_symbol():
            found = "%s (%s)" % (symbol_as_str(self._found_sym), self._text)
        else:
            found = symbol_as_str(self._found_sym)
        msg += ": %s" % self._raw_buffer

        expected = self._expected_sym_str()

        return (msg % {
            'file'       : self._file_name,
            'line'       : self._source_coordinate.get_start_line(),
            'column'     : self._source_coordinate.get_start_column(),
            'expected'   : expected,
            'found'      : found})


class ParseErrorSymList(ParseError):

    def __init__(self, message, expected_syms, parser):
        ParseError.__init__(self, message, 0, parser)
        self._expected_syms = expected_syms

    def _expected_sym_str(self):
        return  ", ".join([symbol_as_str(x) for x in self._expected_syms])
