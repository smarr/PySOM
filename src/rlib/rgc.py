try:
    from rpython.rlib.rgc import collect
except ImportError:
    "NOT_RPYTHON"
    def collect():
        pass
