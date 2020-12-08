import types

import sys

if sys.version_info.major > 2:
    str_type = str
else:
    str_type = (str, unicode)

try:
    from rpython.rlib.objectmodel import we_are_translated, compute_identity_hash, compute_hash, instantiate
    from rpython.rlib.longlong2float import longlong2float, float2longlong
except ImportError:
    "NOT_RPYTHON"
    def we_are_translated():
        return False

    def compute_identity_hash(x):
        assert x is not None
        return object.__hash__(x)

    def compute_hash(x):
        if isinstance(x, str_type):
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

    def instantiate(cls, nonmovable=False):
        "Create an empty instance of 'cls'."
        if isinstance(cls, type):
            return cls.__new__(cls)
        else:
            return types.InstanceType(cls)

    def longlong2float(value):
        return value

    def float2longlong(value):
        return value
