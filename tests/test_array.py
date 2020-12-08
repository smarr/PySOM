import unittest
from som.vm.globals import trueObject
from som.vmobjects.array_strategy import Array, _EmptyStrategy, _ObjectStrategy, \
    _LongStrategy, _PartiallyEmptyStrategy, _BoolStrategy
from som.vmobjects.integer import Integer


class ArrayTest(unittest.TestCase):

    def test_empty_array(self):
        arr = Array.from_size(0)
        self.assertIsInstance(arr._strategy, _EmptyStrategy)

    def test_empty_to_obj(self):
        arr = Array.from_size(1)
        self.assertIsInstance(arr._strategy, _EmptyStrategy)

        arr.set_indexable_field(0, arr)
        self.assertIsInstance(arr._strategy, _ObjectStrategy)
        self.assertIs(arr, arr.get_indexable_field(0))

    def test_empty_to_int(self):
        arr = Array.from_size(1)
        self.assertIsInstance(arr._strategy, _EmptyStrategy)

        int_obj = Integer(42)

        arr.set_indexable_field(0, int_obj)
        self.assertIsInstance(arr._strategy, _LongStrategy)
        self.assertEqual(42, arr.get_indexable_field(0).get_embedded_integer())

    def test_empty_to_bool(self):
        arr = Array.from_size(1)
        self.assertIsInstance(arr._strategy, _EmptyStrategy)

        arr.set_indexable_field(0, trueObject)
        self.assertIsInstance(arr._strategy, _BoolStrategy)
        self.assertEqual(trueObject, arr.get_indexable_field(0))

    def test_copy_and_extend_partially_empty(self):
        arr = Array.from_size(3)

        int_obj = Integer(42)
        arr.set_indexable_field(0, int_obj)
        self.assertIsInstance(arr._strategy, _PartiallyEmptyStrategy)
        new_arr = arr.copy_and_extend_with(int_obj)

        self.assertIsNot(arr, new_arr)
        self.assertEqual(4, new_arr.get_number_of_indexable_fields())
        self.assertIsInstance(new_arr._strategy, _PartiallyEmptyStrategy)
