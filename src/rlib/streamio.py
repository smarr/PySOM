try:
    from rpython.rlib.streamio import open_file_as_stream  # pylint: disable=W
except ImportError:
    "NOT_RPYTHON"

    def open_file_as_stream(file_name, mode):
        return open(file_name, mode)  # pylint: disable=unspecified-encoding


# Taken from PyPy rpython/rlib/streamio.io (Version 7.3.1)
def readall_from_stream(stream):
    bufsize = 8192
    result = []
    while True:
        try:
            data = stream.read(bufsize)
        except OSError:
            # like CPython < 3.4, partial results followed by an error
            # are returned as data
            if not result:
                raise
            break
        if not data:
            break
        result.append(data)
        if bufsize < 4194304:  # 4 Megs
            bufsize <<= 1
    return "".join(result)
