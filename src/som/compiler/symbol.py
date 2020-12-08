# Symbol is a 'lightweight' enum, in Python 3.4, we could use Enum as superclass
class Symbol(object):
    NONE             = -1
    Integer          =  0
    Double           =  1
    Not              =  2
    And              =  3
    Or               =  4
    Star             =  5
    Div              =  6
    Mod              =  7
    Plus             =  8
    Minus            =  9
    Equal            = 10
    More             = 11
    Less             = 12
    Comma            = 13
    At               = 14
    Per              = 15
    NewBlock         = 16
    EndBlock         = 17
    Colon            = 18
    Period           = 19
    Exit             = 20
    Assign           = 21
    NewTerm          = 22
    EndTerm          = 23
    Pound            = 24
    Primitive        = 25
    Separator        = 26
    STString         = 27
    Identifier       = 28
    Keyword          = 29
    KeywordSequence  = 30
    OperatorSequence = 31


def _sorted_symbols(cls):
    "NOT_RPYTHON"
    """This function is only called a single time, at load time of this module.
       For RPython, this means, during translation of the module.
    """
    return [key for value, key in
            sorted([(value, key) for key, value in cls.__dict__.items()
                    if isinstance(value, int)])]
_symbols = _sorted_symbols(Symbol)


def symbol_as_str(symbol):
    index = symbol + 1
    if index > len(_symbols):
        raise ValueError('No Symbol defined for the value %d.' % symbol)
    else:
        return _symbols[index]
