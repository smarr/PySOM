try:
    from rpython.rlib.unroll import unrolling_iterable  # pylint: disable=unused-import
except ImportError:
    "NOT_RPYTHON"

    def unrolling_iterable(values):
        return values
