from som.vmobjects.abstract_object import AbstractObject


class String(AbstractObject):
    _immutable_fields_ = ["_string"]

    def __init__(self, value):
        AbstractObject.__init__(self)
        self._string = value

    def get_embedded_string(self):
        return self._string

    def __str__(self):
        return "\"" + self._string + "\""

    def get_class(self, universe):
        return universe.stringClass
