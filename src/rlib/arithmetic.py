try:
    from rpython.rlib.rarithmetic import ovfcheck, LONG_BIT
    from rpython.rlib.rbigint import rbigint
    from rpython.rlib.rbigint import _divrem as divrem, rbigint as bigint_type
    from rpython.rlib.rarithmetic import string_to_int
    from rpython.rlib.rstring import ParseStringOverflowError

    bigint_from_int = rbigint.fromint
    bigint_from_str = rbigint.fromstr
    int_type = int
except ImportError:
    "NOT_RPYTHON"
    def ovfcheck(value):
        return value

    def bigint_from_int(value):
        return value

    def bigint_from_str(value):
        return int(value)

    def divrem(a, b):
        raise Exception("not yet implemented")

    string_to_int = int

    class ParseStringOverflowError(Exception):
        def __init__(self, parser):
            self.parser = parser

    LONG_BIT = 0x8000000000000000

    import sys
    if sys.version_info.major <= 2:
        int_type = (int, long)
        bigint_type = long
    else:
        int_type = int
        bigint_type = int
