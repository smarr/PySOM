try:
    from rpython.rlib.streamio import Stream, StreamError

    def encode_to_bytes(str_value):
        return str_value
except ImportError:
    "NOT_RPYTHON"
    class Stream(object):
        pass

    class StreamError(Exception):
        pass

    import sys
    if sys.version_info.major > 2:
        def encode_to_bytes(str_value):
            return str_value.encode('utf-8')
    else:
        def encode_to_bytes(str_value):
            return str_value


class StringStream(Stream):
    def __init__(self, string):
        self._string = string
        self.pos     = 0
        self.max     = len(string) - 1

    def write(self, data):
        raise StreamError("StringStream is not writable")

    def truncate(self, size):
        raise StreamError("StringStream is immutable")

    def tell(self):
        return self.pos

    def seek(self, offset, whence):
        if whence == 0:
            self.pos = max(0, offset)
        elif whence == 1:
            self.pos = max(0, self.pos + offset)
        elif whence == 2:
            self.pos = max(0, self.max + offset)
        else:
            raise StreamError("seek(): whence must be 0, 1 or 2")

    def read(self, n):
        assert isinstance(n, int)
        end = self.pos + n
        assert end >= 0
        data = self._string[self.pos:end]
        self.pos += len(data)
        return data
