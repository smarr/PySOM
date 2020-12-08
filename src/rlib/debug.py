try:
    from rpython.rlib.debug import make_sure_not_resized
except ImportError:
    "NOT_RPYTHON"
    def make_sure_not_resized(_):
        pass
