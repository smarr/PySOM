try:
    from rpython.rlib.streamio import open_file_as_stream
except ImportError:
    "NOT_RPYTHON"
    def open_file_as_stream(file_name, mode):
        return open(file_name, mode)
