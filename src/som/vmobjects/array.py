from .abstract_object import AbstractObject
from som.vm.globals import nilObject

from rlib.debug import make_sure_not_resized

from .integer import Integer


class Array(AbstractObject):

    @staticmethod
    def from_size(size):
        return Array(size)

    @staticmethod
    def from_values(values):
        return Array(0, values)

    @staticmethod
    def from_objects(values):
        return Array.from_values(values)

    @staticmethod
    def from_integers(values):
        integers = [Integer(val) for val in values]
        return Array(0, integers)

    _immutable_fields_ = ["_indexable_fields"]

    def __init__(self, number_of_indexable_fields, values = None):
        AbstractObject.__init__(self)

        # Private array of indexable fields
        if values is None:
            self._indexable_fields = [nilObject] * number_of_indexable_fields
        else:
            self._indexable_fields = values
        make_sure_not_resized(self._indexable_fields)

    def get_indexable_field(self, index):
        # Get the indexable field with the given index
        return self._indexable_fields[index]

    def set_indexable_field(self, index, value):
        # Set the indexable field with the given index to the given value
        self._indexable_fields[index] = value

    def get_indexable_fields(self):
        return self._indexable_fields

    def get_number_of_indexable_fields(self):
        # Get the number of indexable fields in this array
        return len(self._indexable_fields)

    def copy(self):
        return Array(0, self._indexable_fields[:])

    def copy_and_extend_with(self, value):
        result = Array(self.get_number_of_indexable_fields() + 1)

        self._copy_indexable_fields_to(result)

        # Insert the given object as the last indexable field in the new array
        result.set_indexable_field(self.get_number_of_indexable_fields(), value)
        return result

    def _copy_indexable_fields_to(self, destination):
        for i, value in enumerate(self._indexable_fields):
            destination._indexable_fields[i] = value

    def get_class(self, universe):
        return universe.arrayClass
