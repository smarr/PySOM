import unittest
from som.vm.globals import trueObject
from som.vmobjects.array import Array
from som.vmobjects.array import _EmptyStrategy  # pylint: disable=protected-access
from som.vmobjects.array import _ObjectStrategy  # pylint: disable=protected-access
from som.vmobjects.array import _LongStrategy  # pylint: disable=protected-access
from som.vmobjects.array import _PartiallyEmptyStrategy  # pylint: disable=W
from som.vmobjects.array import _BoolStrategy  # pylint: disable=protected-access

from som.vmobjects.integer import Integer


class ArrayTest(unittest.TestCase):
    def assert_strategy(self, arr, strategy):
        self.assertIsInstance(arr._strategy, strategy)  # pylint: disable=W

    def test_empty_array(self):
        arr = Array.from_size(0)
        self.assert_strategy(arr, _EmptyStrategy)

    def test_empty_to_obj(self):
        arr = Array.from_size(1)
        self.assert_strategy(arr, _EmptyStrategy)

        arr.set_indexable_field(0, arr)
        self.assert_strategy(arr, _ObjectStrategy)
        self.assertIs(arr, arr.get_indexable_field(0))

    def test_empty_to_int(self):
        arr = Array.from_size(1)
        self.assert_strategy(arr, _EmptyStrategy)

        int_obj = Integer(42)

        arr.set_indexable_field(0, int_obj)
        self.assert_strategy(arr, _LongStrategy)
        self.assertEqual(42, arr.get_indexable_field(0).get_embedded_integer())

    def test_empty_to_bool(self):
        arr = Array.from_size(1)
        self.assert_strategy(arr, _EmptyStrategy)

        arr.set_indexable_field(0, trueObject)
        self.assert_strategy(arr, _BoolStrategy)
        self.assertEqual(trueObject, arr.get_indexable_field(0))

    def test_copy_and_extend_partially_empty(self):
        arr = Array.from_size(3)

        int_obj = Integer(42)
        arr.set_indexable_field(0, int_obj)
        self.assert_strategy(arr, _PartiallyEmptyStrategy)
        new_arr = arr.copy_and_extend_with(int_obj)

        self.assertIsNot(arr, new_arr)
        self.assertEqual(4, new_arr.get_number_of_indexable_fields())
        self.assert_strategy(new_arr, _PartiallyEmptyStrategy)
