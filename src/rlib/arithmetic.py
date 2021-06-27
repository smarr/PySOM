try:
    from rpython.rlib.rarithmetic import ovfcheck, LONG_BIT  # pylint: disable=W
    from rpython.rlib.rbigint import rbigint, _divrem as divrem  # pylint: disable=W
    from rpython.rlib.rbigint import rbigint as BigIntType  # pylint: disable=W
    from rpython.rlib.rarithmetic import string_to_int  # pylint: disable=unused-import
    from rpython.rlib.rstring import ParseStringOverflowError  # pylint: disable=W

    bigint_from_int = rbigint.fromint
    bigint_from_str = rbigint.fromstr
    IntType = int
except ImportError:
    "NOT_RPYTHON"

    def ovfcheck(value):
        return value

    def bigint_from_int(value):
        return value

    def bigint_from_str(value):
        return int(value)

    def divrem(x, y):
        raise Exception("not yet implemented")

    string_to_int = int  # pylint: disable=invalid-name

    class ParseStringOverflowError(Exception):
        def __init__(self, parser):  # pylint: disable=super-init-not-called
            self.parser = parser

    LONG_BIT = 0x8000000000000000

    import sys

    if sys.version_info.major <= 2:
        IntType = (int, long)  # pylint: disable=undefined-variable
        BigIntType = long  # pylint: disable=undefined-variable
    else:
        IntType = int
        BigIntType = int
