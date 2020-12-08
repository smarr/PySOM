class SourceCoordinate(object):

    _immutable_fields_ = ['_start_line', '_start_column', '_char_idx']

    def __init__(self, start_line, start_column, char_idx):
        self._start_line   = start_line
        self._start_column = start_column
        self._char_idx     = char_idx

    def get_start_line(self):
        return self._start_line

    def get_start_column(self):
        return self._start_column


class SourceSection(object):

    _immutable_fields_ = ['_source', '_identifier', '_coord', '_char_length']

    def __init__(self, source = None, identifier = None, coord = None,
                 char_length = 0, file_name = None, source_section = None):
        if source_section:
            self._source      = source_section._source
            self._coord       = source_section._coord
            self._char_length = source_section._char_length
            self._file        = source_section._file
        else:
            self._source      = source
            self._coord       = coord
            self._char_length = char_length
            self._file        = file_name
        self._identifier  = identifier

    def __str__(self):
        return "%s:%d:%d" % (self._file, self._coord.get_start_line(),
                             self._coord.get_start_column())
