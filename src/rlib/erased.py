try:
    from rpython.rlib.rerased import new_erasing_pair  # pylint: disable=unused-import
    from rpython.rlib.rerased import erase_int  # pylint: disable=unused-import
    from rpython.rlib.rerased import unerase_int  # pylint: disable=unused-import
except ImportError:
    "NOT_RPYTHON"

    def new_erasing_pair(name):
        identity = _ErasingPairIdentity(name)

        def erase(x):
            return _Erased(x, identity)

        def unerase(y):
            assert y._identity is identity  # pylint: disable=W
            return y._x  # pylint: disable=W

        return erase, unerase

    def erase_int(val):
        return val

    def unerase_int(val):
        return val

    class _ErasingPairIdentity(object):
        def __init__(self, name):
            self.name = name

    class _Erased(object):
        def __init__(self, x, identity):
            self._x = x
            self._identity = identity

        def __str__(self):
            return "Erased(" + str(self._x) + ", " + self._identity.name + ")"
