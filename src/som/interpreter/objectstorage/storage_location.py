from rlib.jit import we_are_jitted
from rlib.objectmodel import longlong2float, float2longlong
from som.interpreter.objectstorage.layout_transitions import (
    UninitializedStorageLocationException,
    GeneralizeStorageLocationException,
)
from som.vm.globals import nilObject

from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer

NUMBER_OF_PRIMITIVE_FIELDS = 5
NUMBER_OF_POINTER_FIELDS = 5


class _BasicLocation(object):
    _immutable_fields_ = [
        "field_idx",
        "access_idx",
        "mask",
        "is_set_fn",
        "read_fn",
        "write_fn",
    ]

    def __init__(self, field_idx, access_idx, mask, is_set_fn, read_fn, write_fn):
        self.field_idx = field_idx
        self.access_idx = access_idx
        self.mask = mask
        self.is_set_fn = is_set_fn
        self.read_fn = read_fn
        self.write_fn = write_fn


class _Location(_BasicLocation):
    _immutable_fields_ = [
        "store_idx",
        "storage_type",
    ]

    def __init__(
        self,
        field_idx,
        store_idx,
        access_idx,
        is_set_fn,
        read_fn,
        write_fn,
        storage_type,
    ):
        _BasicLocation.__init__(
            self,
            field_idx,
            access_idx,
            _get_primitive_field_mask(store_idx),
            is_set_fn,
            read_fn,
            write_fn,
        )
        self.store_idx = store_idx
        self.storage_type = storage_type

    def create_access_node(self, layout, next_entry):
        return _AccessNode(
            layout,
            self.field_idx,
            self.access_idx,
            self.mask,
            self.is_set_fn,
            self.read_fn,
            self.write_fn,
            next_entry,
        )

    def __str__(self):
        return "Location(" + str(self.field_idx) + ")"


class _AccessNode(_BasicLocation):
    _immutable_fields_ = [
        "layout",
        "next_entry?",
    ]

    def __init__(
        self,
        layout,
        field_idx,
        access_idx,
        mask,
        is_set_fn,
        read_fn,
        write_fn,
        next_entry,
    ):
        _BasicLocation.__init__(
            self, field_idx, access_idx, mask, is_set_fn, read_fn, write_fn
        )
        self.layout = layout
        self.next_entry = next_entry


def _get_primitive_field_mask(store_idx):
    # might even be 64 bit, depending on the int size,
    # should use some RPython constant here
    if 0 <= store_idx < 32:
        return 1 << store_idx
    return 0


def create_location_for_long(field_idx, prim_field_idx):
    if prim_field_idx < NUMBER_OF_PRIMITIVE_FIELDS:
        return _Location(
            field_idx,
            prim_field_idx,
            -1,
            _prim_is_set,
            _long_direct_read[prim_field_idx],
            _long_direct_write[prim_field_idx],
            Integer,
        )
    return _Location(
        field_idx,
        prim_field_idx,
        prim_field_idx - NUMBER_OF_PRIMITIVE_FIELDS,
        _prim_is_set,
        _long_array_read,
        _long_array_write,
        Integer,
    )


def create_location_for_double(field_idx, prim_field_idx):
    if prim_field_idx < NUMBER_OF_PRIMITIVE_FIELDS:
        return _Location(
            field_idx,
            prim_field_idx,
            -1,
            _prim_is_set,
            _double_direct_read[prim_field_idx],
            _double_direct_write[prim_field_idx],
            Double,
        )
    return _Location(
        field_idx,
        prim_field_idx,
        prim_field_idx - NUMBER_OF_PRIMITIVE_FIELDS,
        _prim_is_set,
        _double_array_read,
        _double_array_write,
        Double,
    )


def create_location_for_object(field_idx, ptr_field_idx):
    from som.vmobjects.object_with_layout import ObjectWithLayout

    if ptr_field_idx < NUMBER_OF_POINTER_FIELDS:
        return _Location(
            field_idx,
            ptr_field_idx,
            -1,
            _object_is_set,
            _object_direct_read[ptr_field_idx],
            _object_direct_write[ptr_field_idx],
            ObjectWithLayout,
        )
    return _Location(
        field_idx,
        ptr_field_idx,
        ptr_field_idx - NUMBER_OF_POINTER_FIELDS,
        _object_is_set,
        _object_array_read,
        _object_array_write,
        ObjectWithLayout,
    )


def create_location_for_unwritten(field_idx):
    return _Location(
        field_idx, -1, -1, _unwritten_is_set, _unwritten_read, _unwritten_write, None
    )


def create_generic_access_node(field_idx):
    return _AccessNode(
        None, field_idx, -1, -1, _generic_is_set, _generic_read, _generic_write, None
    )


def _generic_is_set(node, obj):
    location = obj.get_location(node.field_idx)
    return location.is_set_fn(location, obj)


def _generic_read(node, obj):
    return obj.get_field(node.field_idx)


def _generic_write(node, obj, value):
    obj.set_field(node.field_idx, value)


def _unwritten_is_set(_node, _obj):
    return False


def _unwritten_read(_node, _obj):
    return nilObject


def _unwritten_write(_node, _obj, value):
    if value is not nilObject:
        raise UninitializedStorageLocationException()


def _make_object_direct_read(field_idx):
    def read_location(_node, obj):
        # assert isinstance(obj, ObjectWithLayout)
        return getattr(obj, "_field" + str(field_idx))

    return read_location


def _make_object_direct_write(field_idx):
    def write_location(_node, obj, value):  # pylint: disable=no-self-use
        assert value is not None
        # assert isinstance(obj, ObjectWithLayout)
        setattr(obj, "_field" + str(field_idx), value)

    return write_location


def _object_is_set(_node, _obj):
    return True


def _object_array_read(node, obj):
    return obj.fields[node.access_idx]


def _object_array_write(node, obj, value):
    # assert isinstance(obj, ObjectWithLayout)
    assert value is not None
    obj.fields[node.access_idx] = value


def _unset_or_generalize(node, obj, value):
    if value is nilObject:
        obj.mark_prim_as_unset(node.mask)
    else:
        if we_are_jitted():
            assert False
        raise GeneralizeStorageLocationException()


def _prim_is_set(node, obj):
    return obj.is_primitive_set(node.mask)


def _make_double_direct_read(field_idx):
    def read_location(node, obj):
        # assert isinstance(obj, ObjectWithLayout)
        if obj.is_primitive_set(node.mask):
            double_val = longlong2float(getattr(obj, "prim_field" + str(field_idx)))
            return Double(double_val)
        return nilObject

    return read_location


def _make_double_direct_write(field_idx):
    def write_location(node, obj, value):
        assert value is not None
        assert isinstance(value, AbstractObject)

        if isinstance(value, Double):
            setattr(
                obj,
                "prim_field" + str(field_idx),
                float2longlong(value.get_embedded_double()),
            )
            obj.mark_prim_as_set(node.mask)
        else:
            _unset_or_generalize(node, obj, value)

    return write_location


def _make_long_direct_read(field_idx):
    def read_location(node, obj):
        # assert isinstance(obj, ObjectWithLayout)
        if obj.is_primitive_set(node.mask):
            return Integer(getattr(obj, "prim_field" + str(field_idx)))
        return nilObject

    return read_location


def _make_long_direct_write(field_idx):
    def write_location(node, obj, value):
        assert value is not None
        assert isinstance(value, AbstractObject)

        if isinstance(value, Integer):
            setattr(obj, "prim_field" + str(field_idx), value.get_embedded_integer())
            obj.mark_prim_as_set(node.mask)
        else:
            _unset_or_generalize(node, obj, value)

    return write_location


def _long_array_read(node, obj):
    if obj.is_primitive_set(node.mask):
        return Integer(obj.prim_fields[node.access_idx])
    return nilObject


def _long_array_write(node, obj, value):
    if isinstance(value, Integer):
        obj.prim_fields[node.access_idx] = value.get_embedded_integer()
        obj.mark_prim_as_set(node.mask)
    else:
        _unset_or_generalize(node, obj, value)


def _double_array_read(node, obj):
    if obj.is_primitive_set(node.mask):
        val = longlong2float(obj.prim_fields[node.access_idx])
        return Double(val)
    return nilObject


def _double_array_write(node, obj, value):
    if isinstance(value, Double):
        val = float2longlong(value.get_embedded_double())
        obj.prim_fields[node.access_idx] = val
        obj.mark_prim_as_set(node.mask)
    else:
        _unset_or_generalize(node, obj, value)


_object_direct_read = [
    _make_object_direct_read(i + 1) for i in range(NUMBER_OF_POINTER_FIELDS)
]
_object_direct_write = [
    _make_object_direct_write(i + 1) for i in range(NUMBER_OF_POINTER_FIELDS)
]

_long_direct_read = [
    _make_long_direct_read(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]
_long_direct_write = [
    _make_long_direct_write(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]

_double_direct_read = [
    _make_double_direct_read(i + 1) for i in range(NUMBER_OF_POINTER_FIELDS)
]
_double_direct_write = [
    _make_double_direct_write(i + 1) for i in range(NUMBER_OF_POINTER_FIELDS)
]
