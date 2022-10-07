from rlib.arithmetic import ovfcheck
from rlib.objectmodel import longlong2float, float2longlong
from som.interpreter.objectstorage.layout_transitions import (
    UninitializedStorageLocationException,
    GeneralizeStorageLocationException,
)
from som.vm.globals import nilObject

from som.vmobjects.double import Double
from som.vmobjects.integer import Integer

NUMBER_OF_PRIMITIVE_FIELDS = 5
NUMBER_OF_POINTER_FIELDS = 5


class _Location(object):
    _immutable_fields_ = [
        "field_idx",
        "access_idx",
        "mask",
        "is_set_fn",
        "read_fn",
        "inc_fn",
        "write_fn",
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
        inc_fn,
        write_fn,
        storage_type,
    ):
        self.field_idx = field_idx
        self.access_idx = access_idx
        self.mask = _get_primitive_field_mask(store_idx)
        self.is_set_fn = is_set_fn
        self.read_fn = read_fn
        self.inc_fn = inc_fn
        self.write_fn = write_fn
        self.store_idx = store_idx
        self.storage_type = storage_type

    def __str__(self):
        return "Location(" + str(self.field_idx) + ")"


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
            _long_direct_inc[prim_field_idx],
            _long_direct_write[prim_field_idx],
            Integer,
        )
    return _Location(
        field_idx,
        prim_field_idx,
        prim_field_idx - NUMBER_OF_PRIMITIVE_FIELDS,
        _prim_is_set,
        _long_array_read,
        _long_array_inc,
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
            _double_direct_inc[prim_field_idx],
            _double_direct_write[prim_field_idx],
            Double,
        )
    return _Location(
        field_idx,
        prim_field_idx,
        prim_field_idx - NUMBER_OF_PRIMITIVE_FIELDS,
        _prim_is_set,
        _double_array_read,
        _double_array_inc,
        _double_array_write,
        Double,
    )


def create_location_for_object(field_idx, ptr_field_idx):
    from som.vmobjects.object_with_layout import Object

    if ptr_field_idx < NUMBER_OF_POINTER_FIELDS:
        return _Location(
            field_idx,
            ptr_field_idx,
            -1,
            _object_is_set,
            _object_direct_read[ptr_field_idx],
            _object_direct_inc[ptr_field_idx],
            _object_direct_write[ptr_field_idx],
            Object,
        )
    return _Location(
        field_idx,
        ptr_field_idx,
        ptr_field_idx - NUMBER_OF_POINTER_FIELDS,
        _object_is_set,
        _object_array_read,
        _object_array_inc,
        _object_array_write,
        Object,
    )


def create_location_for_unwritten(field_idx):
    return _Location(
        field_idx,
        -1,
        -1,
        _unwritten_is_set,
        _unwritten_read,
        _unwritten_inc,
        _unwritten_write,
        None,
    )


def _unwritten_is_set(_node, _obj):
    return False


def _unwritten_read(_node, _obj):
    return nilObject


def _unwritten_inc(_node, _obj):
    raise UninitializedStorageLocationException()


def _unwritten_write(_node, _obj, value):
    if value is not nilObject:
        raise UninitializedStorageLocationException()


def _make_object_direct_read(field_idx):
    def read_location(_node, obj):
        return getattr(obj, "_field" + str(field_idx))

    return read_location


def _make_object_direct_inc(field_idx):
    def inc_location(_node, obj):
        field_name = "_field" + str(field_idx)
        val = getattr(obj, field_name)
        new_val = val.prim_inc()
        setattr(obj, field_name, new_val)
        return new_val

    return inc_location


def _make_object_direct_write(field_idx):
    def write_location(_node, obj, value):
        setattr(obj, "_field" + str(field_idx), value)

    return write_location


def _object_is_set(_node, _obj):
    return True


def _object_array_read(node, obj):
    return obj.fields[node.access_idx]


def _object_array_inc(node, obj):
    val = obj.fields[node.access_idx]
    new_val = val.prim_inc()
    obj.fields[node.access_idx] = new_val
    return new_val


def _object_array_write(node, obj, value):
    obj.fields[node.access_idx] = value


def _unset_or_generalize(node, obj, value):
    if value is nilObject:
        obj.mark_prim_as_unset(node.mask)
    else:
        raise GeneralizeStorageLocationException()


def _prim_is_set(node, obj):
    return obj.is_primitive_set(node.mask)


def _make_double_direct_read(field_idx):
    def read_location(node, obj):
        if obj.is_primitive_set(node.mask):
            double_val = longlong2float(getattr(obj, "prim_field" + str(field_idx)))
            return Double(double_val)
        return nilObject

    return read_location


def _make_double_direct_inc(field_idx):
    def inc_location(node, obj):
        if obj.is_primitive_set(node.mask):
            field_name = "prim_field" + str(field_idx)
            double_val = longlong2float(getattr(obj, field_name))
            double_val += 1.0
            setattr(obj, field_name, float2longlong(double_val))
            return Double(double_val)
        raise NotImplementedError()

    return inc_location


def _make_double_direct_write(field_idx):
    def write_location(node, obj, value):
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
        if obj.is_primitive_set(node.mask):
            return Integer(getattr(obj, "prim_field" + str(field_idx)))
        return nilObject

    return read_location


def _make_long_direct_inc(field_idx):
    def read_location(node, obj):
        if obj.is_primitive_set(node.mask):
            field_name = "prim_field" + str(field_idx)
            val = getattr(obj, field_name)
            try:
                result = ovfcheck(val + 1)
                setattr(obj, field_name, result)
                return Integer(result)
            except OverflowError:
                raise NotImplementedError()
        raise NotImplementedError()

    return read_location


def _make_long_direct_write(field_idx):
    def write_location(node, obj, value):
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


def _long_array_inc(node, obj):
    if obj.is_primitive_set(node.mask):
        val = obj.prim_fields[node.access_idx]
        try:
            result = ovfcheck(val + 1)
            obj.prim_fields[node.access_idx] = result
            return Integer(result)
        except OverflowError:
            raise NotImplementedError()
    raise NotImplementedError()


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


def _double_array_inc(node, obj):
    if obj.is_primitive_set(node.mask):
        val = longlong2float(obj.prim_fields[node.access_idx])
        val += 1.0
        obj.prim_fields[node.access_idx] = float2longlong(val)
        return Double(val)
    raise NotImplementedError()


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
_object_direct_inc = [
    _make_object_direct_inc(i + 1) for i in range(NUMBER_OF_POINTER_FIELDS)
]
_object_direct_write = [
    _make_object_direct_write(i + 1) for i in range(NUMBER_OF_POINTER_FIELDS)
]

_long_direct_read = [
    _make_long_direct_read(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]
_long_direct_inc = [
    _make_long_direct_inc(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]
_long_direct_write = [
    _make_long_direct_write(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]

_double_direct_read = [
    _make_double_direct_read(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]
_double_direct_inc = [
    _make_double_direct_inc(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]
_double_direct_write = [
    _make_double_direct_write(i + 1) for i in range(NUMBER_OF_PRIMITIVE_FIELDS)
]
