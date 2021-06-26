import sys

if sys.version_info.major > 2:
    StrType = str
else:
    StrType = (str, unicode)  # pylint: disable=undefined-variable

try:
    from rpython.rlib.objectmodel import we_are_translated  # pylint: disable=W
    from rpython.rlib.objectmodel import compute_identity_hash  # pylint: disable=W
    from rpython.rlib.objectmodel import compute_hash  # pylint: disable=unused-import
    from rpython.rlib.longlong2float import longlong2float  # pylint: disable=W
    from rpython.rlib.longlong2float import float2longlong  # pylint: disable=W
except ImportError:
    "NOT_RPYTHON"

    def we_are_translated():
        return False

    def compute_identity_hash(x):
        assert x is not None
        return object.__hash__(x)

    def compute_hash(x):
        if isinstance(x, StrType):
            return hash(x)
        if isinstance(x, int):
            return x
        if isinstance(x, float):
            return hash(x)
        if isinstance(x, tuple):
            return hash(x)
        if x is None:
            return 0
        return compute_identity_hash(x)

    def longlong2float(value):
        return value

    def float2longlong(value):
        return value
