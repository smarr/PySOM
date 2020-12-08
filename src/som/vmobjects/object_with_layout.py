from rlib.jit import promote, we_are_jitted
from som.interpreter.objectstorage.object_layout import ObjectLayout
from som.interpreter.objectstorage.layout_transitions import \
    UninitializedStorageLocationException, GeneralizeStorageLocationException
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object_without_fields import ObjectWithoutFields
from som.vm.globals import nilObject

_EMPTY_LIST = []


class ObjectWithLayout(ObjectWithoutFields):

    _immutable_fields_ = ["_object_layout?",
                          "_fields?", "_primFields?"]

    # Static field indices and number of object fields
    NUMBER_OF_OBJECT_FIELDS = 0

    def __init__(self, obj_class, number_of_fields = NUMBER_OF_OBJECT_FIELDS):
        cls = obj_class if obj_class is not None else nilObject
        ObjectWithoutFields.__init__(self, cls)

        if obj_class is not None:
            self._object_layout = obj_class.get_layout_for_instances()
        else:
            self._object_layout = ObjectLayout(number_of_fields)

        # IMPORTANT: when changing the number of preallocated fields,
        # you'll also need to update storage_location.py's constants:
        #  NUMBER_OF_PRIMITIVE_FIELDS and NUMBER_OF_POINTER_FIELDS
        self._field1 = nilObject
        self._field2 = nilObject
        self._field3 = nilObject
        self._field4 = nilObject
        self._field5 = nilObject

        self._primField1 = 0
        self._primField2 = 0
        self._primField3 = 0
        self._primField4 = 0
        self._primField5 = 0

        assert (self._object_layout.get_number_of_fields() == number_of_fields)
                # TODO:
                # or obj_class is None
                # or not obj_class._universe.is_object_system_initialized())

        n = self._object_layout.get_number_of_used_extended_prim_locations()
        if n > 0:
            self._primFields = [0] * n
        else:
            self._primFields = _EMPTY_LIST

        self._primitive_used_map = 0

        n = self._object_layout.get_number_of_used_extended_ptr_locations()
        if n > 0:
            self._fields = [nilObject] * n
        else:
            self._fields = None  ## for some reason _EMPTY_LIST doesn't typecheck here

    def get_object_layout(self):
        return promote(self._object_layout)

    def _get_all_fields(self):
        assert not we_are_jitted()
        num_fields = self._object_layout.get_number_of_fields()
        field_values = [None] * num_fields
        for i in range(0, num_fields):
            if self._is_field_set(i):
                field_values[i] = self.get_field(i)
        return field_values

    def _set_all_fields(self, field_values):
        assert not we_are_jitted()
        self._field1 = self._field2 = self._field3 = self._field4 = self._field5 = nilObject
        self._primField1 = self._primField2 = self._primField3 = self._primField4 = self._primField5 = 1234567890

        for i in range(0, self._object_layout.get_number_of_fields()):
            if field_values[i] is None:
                self.set_field(i, nilObject)
            else:
                self.set_field(i, field_values[i])

    def update_layout_to_match_class(self):
        assert not we_are_jitted()
        class_layout = self._class.get_layout_for_instances()
        assert self._object_layout.get_number_of_fields() == class_layout.get_number_of_fields()

        if self._object_layout is not class_layout:
            self._set_layout_and_transfer_fields(class_layout)
            return True
        else:
            return False

    def _set_layout_and_transfer_fields(self, layout):
        assert not we_are_jitted()
        field_values = self._get_all_fields()
        self._object_layout = layout

        n = self._object_layout.get_number_of_used_extended_prim_locations()
        if n > 0:
            self._primFields = [0] * n
        else:
            self._primFields = _EMPTY_LIST

        self._primitive_used_map = 0

        n = self._object_layout.get_number_of_used_extended_ptr_locations()
        if n > 0:
            self._fields = [nilObject] * n
        else:
            self._fields = None

        self._set_all_fields(field_values)

    def _update_layout_with_initialized_field(self, idx, field_type):
        assert not we_are_jitted()
        layout = self._class.update_instance_layout_with_initialized_field(
            idx, field_type)

        assert layout is not self._object_layout

        self._set_layout_and_transfer_fields(layout)

    def _update_layout_with_generalized_field(self, idx):
        assert not we_are_jitted()
        layout = self._class.update_instance_layout_with_generalized_field(idx)

        assert layout is not self._object_layout
        self._set_layout_and_transfer_fields(layout)

    def get_field_name(self, index):
        # Get the name of the field with the given index
        return self._class.get_instance_field_name(index)

    def get_field_index(self, name):
        # Get the index for the field with the given name
        return self._class.lookup_field_index(name)

    def get_number_of_fields(self):
        # Get the number of fields in this object
        return len(self._fields)

    def is_primitive_set(self, mask):
        return (promote(self._primitive_used_map) & mask) != 0

    def mark_prim_as_set(self, mask):
        if (self._primitive_used_map & mask) == 0:
            self._primitive_used_map |= mask

    def mark_prim_as_unset(self, mask):
        if (self._primitive_used_map & mask) != 0:
            self._primitive_used_map &= ~mask

    def get_location(self, field_idx):
        field_idx = promote(field_idx)
        location = promote(self._object_layout).get_storage_location(field_idx)
        assert location is not None
        return location

    def _is_field_set(self, field_idx):
        return self.get_location(field_idx).is_set(self)

    def get_field(self, field_idx):
        # Get the field with the given index
        assert isinstance(field_idx, int)

        return self.get_location(field_idx).read_location(self)

    def set_field(self, field_idx, value):
        # Set the field with the given index to the given value
        assert isinstance(field_idx, int)
        assert isinstance(value, AbstractObject)

        location = self.get_location(field_idx)

        try:
            location.write_location(self, value)
            return
        except UninitializedStorageLocationException:
            self._update_layout_with_initialized_field(field_idx,
                                                       value.__class__)
        except GeneralizeStorageLocationException:
            self._update_layout_with_generalized_field(field_idx)
        self._set_field_after_layout_change(field_idx, value)

    def _set_field_after_layout_change(self, field_idx, value):
        assert not we_are_jitted()

        location = self.get_location(field_idx)
        # we aren't handling potential exceptions here, because,
        # they should not happen by construction
        location.write_location(self, value)
