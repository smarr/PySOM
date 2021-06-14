try:
    from rpython.rlib.rerased import new_erasing_pair  # pylint: disable=unused-import
except ImportError:
    "NOT_RPYTHON"

    def new_erasing_pair(_name):
        def erase(x):
            return x

        def unerase(y):
            return y

        return erase, unerase
