from rlib.jit import we_are_jitted
from rlib.objectmodel import longlong2float, float2longlong
from som.interpreter.objectstorage.layout_transitions import \
    UninitializedStorageLocationException, GeneralizeStorageLocationException
from som.vm.globals import nilObject

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer


NUMBER_OF_PRIMITIVE_FIELDS = 5
NUMBER_OF_POINTER_FIELDS   = 5


def get_primitive_field_mask(field_idx):
    # might even be 64 bit, depending on the int size,
    # should use some RPython constant here
    assert 0 <= field_idx < 32
    return 1 << field_idx


def create_location_for_long(layout, prim_field_idx):
    if prim_field_idx < NUMBER_OF_PRIMITIVE_FIELDS:
        return _long_direct_class[prim_field_idx](layout, prim_field_idx)
    else:
        return LongArrayStorageLocation(layout, prim_field_idx)


def create_location_for_double(layout, prim_field_idx):
    if prim_field_idx < NUMBER_OF_PRIMITIVE_FIELDS:
        return _double_direct_class[prim_field_idx](layout, prim_field_idx)
    else:
        return DoubleArrayStorageLocation(layout, prim_field_idx)


def create_location_for_object(layout, ptr_field_idx):
    if ptr_field_idx < NUMBER_OF_POINTER_FIELDS:
        return _object_direct_class[ptr_field_idx](layout, ptr_field_idx)
    else:
        return ObjectArrayStorageLocation(layout, ptr_field_idx)


def create_location_for_unwritten_value(layout):
    return UnwrittenStorageLocation(layout)


class _AbstractStorageLocation(object):

    _immutable_fields_ = ['_layout']

    def __init__(self, layout):
        self._layout    = layout


class UnwrittenStorageLocation(_AbstractStorageLocation):

    def is_set(self, obj):
        return False

    def read_location(self, obj):
        return nilObject

    def write_location(self, obj, value):
        if value is not nilObject:
            raise UninitializedStorageLocationException()


class _AbstractObjectStorageLocation(_AbstractStorageLocation):
    _immutable_fields_ = ["_field_idx"]

    def __init__(self, layout, field_idx):
        _AbstractStorageLocation.__init__(self, layout)
        self._field_idx = field_idx

    def is_set(self, obj):
        return True


def _make_object_direct_storage_location(field_idx):
    class _ObjectDirectStorageLocationI(_AbstractObjectStorageLocation):
        def read_location(self, obj):
            #assert isinstance(obj, ObjectWithLayout)
            return getattr(obj, "_field" + str(field_idx))

        def write_location(self, obj, value):
            assert value is not None
            #assert isinstance(obj, ObjectWithLayout)
            setattr(obj, "_field" + str(field_idx), value)
    return _ObjectDirectStorageLocationI


class ObjectArrayStorageLocation(_AbstractObjectStorageLocation):

    _immutable_fields_ = ['_ext_idx']

    def __init__(self, layout, field_idx):
        _AbstractObjectStorageLocation.__init__(self, layout, field_idx)
        self._ext_idx = field_idx - NUMBER_OF_POINTER_FIELDS

    def read_location(self, obj):
        #assert isinstance(obj, ObjectWithLayout)
        return obj._fields[self._ext_idx]

    def write_location(self, obj, value):
        #assert isinstance(obj, ObjectWithLayout)
        assert value is not None
        obj._fields[self._ext_idx] = value


class _AbstractPrimitiveStorageLocation(_AbstractStorageLocation):

    _immutable_fields_ = ['_mask']

    def __init__(self, layout, field_idx):
        _AbstractStorageLocation.__init__(self, layout)
        self._mask = get_primitive_field_mask(field_idx)

    def is_set(self, obj):
        return obj.is_primitive_set(self._mask)

    def _mark_as_set(self, obj):
        obj.mark_prim_as_set(self._mask)

    def _mark_as_unset(self, obj):
        obj.mark_prim_as_unset(self._mask)

    def _unset_or_generalize(self, obj, value):
        if value is nilObject:
            self._mark_as_unset(obj)
        else:
            if we_are_jitted():
                assert False
            raise GeneralizeStorageLocationException()


def _make_double_direct_storage_location(field_idx):
    class _DoubleDirectStorageLocationI(_AbstractPrimitiveStorageLocation):
        def read_location(self, obj):
            # assert isinstance(obj, ObjectWithLayout)
            if self.is_set(obj):
                double_val = longlong2float(
                    getattr(obj, "_primField" + str(field_idx)))
                return Double(double_val)
            else:
                return nilObject

        def write_location(self, obj, value):
            assert value is not None
            assert isinstance(value, AbstractObject)

            if isinstance(value, Double):
                setattr(obj, "_primField" + str(field_idx),
                        float2longlong(value.get_embedded_double()))
                self._mark_as_set(obj)
            else:
                self._unset_or_generalize(obj, value)
    return _DoubleDirectStorageLocationI


def _make_long_direct_storage_location(field_idx):
    class _LongDirectStorageLocationI(_AbstractPrimitiveStorageLocation):
        def read_location(self, obj):
            # assert isinstance(obj, ObjectWithLayout)

            if self.is_set(obj):
                return Integer(getattr(obj, "_primField" + str(field_idx)))
            else:
                return nilObject

        def write_location(self, obj, value):
            assert value is not None
            assert isinstance(value, AbstractObject)

            if isinstance(value, Integer):
                setattr(obj, "_primField" + str(field_idx),
                        value.get_embedded_integer())
                self._mark_as_set(obj)
            else:
                self._unset_or_generalize(obj, value)
    return _LongDirectStorageLocationI


class _AbstractPrimitiveArrayStorageLocation(_AbstractPrimitiveStorageLocation):

    _immutable_fields_ = ['_ext_idx']

    def __init__(self, layout, field_idx):
        _AbstractPrimitiveStorageLocation.__init__(self, layout, field_idx)
        self._ext_idx = field_idx - NUMBER_OF_PRIMITIVE_FIELDS


class LongArrayStorageLocation(_AbstractPrimitiveArrayStorageLocation):

    def read_location(self, obj):
        if self.is_set(obj):
            return Integer(obj._primFields[self._ext_idx])
        else:
            return nilObject

    def write_location(self, obj, value):
        if isinstance(value, Integer):
            obj._primFields[self._ext_idx] = value.get_embedded_integer()
            self._mark_as_set(obj)
        else:
            self._unset_or_generalize(obj, value)


class DoubleArrayStorageLocation(_AbstractPrimitiveArrayStorageLocation):

    def read_location(self, obj):
        if self.is_set(obj):
            val = longlong2float(obj._primFields[self._ext_idx])
            return Double(val)
        else:
            return nilObject

    def write_location(self, obj, value):
        if isinstance(value, Double):
            val = float2longlong(value.get_embedded_double())
            obj._primFields[self._ext_idx] = val
            self._mark_as_set(obj)
        else:
            self._unset_or_generalize(obj, value)

_object_direct_class = [_make_object_direct_storage_location(i + 1)
                        for i in range(NUMBER_OF_POINTER_FIELDS)]
_long_direct_class   = [_make_long_direct_storage_location(i + 1)
                        for i in range(NUMBER_OF_PRIMITIVE_FIELDS)]
_double_direct_class = [_make_double_direct_storage_location(i + 1)
                        for i in range(NUMBER_OF_POINTER_FIELDS)]
