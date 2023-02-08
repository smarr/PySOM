class SourceCoordinate(object):
    _immutable_fields_ = ["start_line", "start_column", "char_idx"]

    def __init__(self, start_line, start_column, char_idx):
        self.start_line = start_line
        self.start_column = start_column
        self.char_idx = char_idx


class SourceSection(object):
    _immutable_fields_ = ["source", "identifier", "coord", "char_length"]

    def __init__(
        self,
        source=None,
        identifier=None,
        coord=None,
        char_length=0,
        file_name=None,
        source_section=None,
    ):
        if source_section:
            self.source = source_section.source
            self.coord = source_section.coord
            self.char_length = source_section.char_length
            self.file = source_section.file
        else:
            self.source = source
            self.coord = coord
            self.char_length = char_length
            self.file = file_name
        self.identifier = identifier

    def __str__(self):
        return "%s:%d:%d" % (self.file, self.coord.start_line, self.coord.start_column)
