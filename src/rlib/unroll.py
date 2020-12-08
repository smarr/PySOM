try:
    from rpython.rlib.unroll import unrolling_iterable
except ImportError:
    "NOT_RPYTHON"
    def unrolling_iterable(values):
        return values
