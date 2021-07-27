try:
    from rpython.rlib.rgc import collect  # pylint: disable=unused-import
    from rpython.rlib.rgc import disable  # pylint: disable=unused-import
    from rpython.rlib.rgc import isenabled  # pylint: disable=unused-import
except ImportError:
    "NOT_RPYTHON"

    def collect():
        pass

    def disable():
        pass

    def isenabled():
        return 1
