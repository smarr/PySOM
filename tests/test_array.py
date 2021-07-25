from som.vm.globals import trueObject
from som.vmobjects.array import Array
from som.vmobjects.array import _empty_strategy  # pylint: disable=protected-access
from som.vmobjects.array import _obj_strategy  # pylint: disable=protected-access
from som.vmobjects.array import _long_strategy  # pylint: disable=protected-access
from som.vmobjects.array import _partially_empty_strategy  # pylint: disable=W
from som.vmobjects.array import _bool_strategy  # pylint: disable=protected-access

from som.vmobjects.integer import Integer


def test_empty_array():
    arr = Array.from_size(0)
    assert arr.strategy is _empty_strategy


def test_empty_to_obj():
    arr = Array.from_size(1)
    assert arr.strategy is _empty_strategy

    arr.set_indexable_field(0, arr)
    assert arr.strategy is _obj_strategy
    assert arr is arr.get_indexable_field(0)


def test_empty_to_int():
    arr = Array.from_size(1)
    assert arr.strategy is _empty_strategy

    int_obj = Integer(42)

    arr.set_indexable_field(0, int_obj)
    assert arr.strategy is _long_strategy
    assert arr.get_indexable_field(0).get_embedded_integer() == 42


def test_empty_to_bool():
    arr = Array.from_size(1)
    assert arr.strategy is _empty_strategy

    arr.set_indexable_field(0, trueObject)
    assert arr.strategy is _bool_strategy
    assert trueObject is arr.get_indexable_field(0)


def test_copy_and_extend_partially_empty():
    arr = Array.from_size(3)

    int_obj = Integer(42)
    arr.set_indexable_field(0, int_obj)
    assert arr.strategy is _partially_empty_strategy
    new_arr = arr.copy_and_extend_with(int_obj)

    assert arr is not new_arr
    assert new_arr.get_number_of_indexable_fields() == 4
    assert new_arr.strategy is _partially_empty_strategy
