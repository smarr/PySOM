from som.interpreter.objectstorage.storage_location import \
    create_location_for_long, create_location_for_double, \
    create_location_for_object, create_location_for_unwritten_value, \
    NUMBER_OF_POINTER_FIELDS, NUMBER_OF_PRIMITIVE_FIELDS, \
    _AbstractStorageLocation
from som.vmobjects.double  import Double
from som.vmobjects.integer import Integer


class ObjectLayout(object):

    _immutable_fields_ = ["_for_class", "_prim_locations_used",
                          "_ptr_locations_used", "_total_locations",
                          "_storage_locations[*]", "_storage_types[*]"]

    def __init__(self, number_of_fields, for_class = None,
                 known_types = None):
        assert number_of_fields >= 0
        from som.vmobjects.object_with_layout import ObjectWithLayout
        self._for_class = for_class
        self._storage_types = known_types or [None] * number_of_fields
        self._total_locations = number_of_fields
        self._storage_locations = [None] * number_of_fields

        next_free_prim_idx = 0
        next_free_ptr_idx  = 0

        for i in range(0, number_of_fields):
            storage_type = self._storage_types[i]

            if storage_type is Integer:
                storage = create_location_for_long(self, next_free_prim_idx)
                next_free_prim_idx += 1
            elif storage_type is Double:
                storage = create_location_for_double(self, next_free_prim_idx)
                next_free_prim_idx += 1
            elif storage_type is ObjectWithLayout:
                storage = create_location_for_object(self, next_free_ptr_idx)
                next_free_ptr_idx += 1
            else:
                assert storage_type is None
                storage = create_location_for_unwritten_value(self)

            assert isinstance(storage, _AbstractStorageLocation)
            self._storage_locations[i] = storage

        self._prim_locations_used = next_free_prim_idx
        self._ptr_locations_used  = next_free_ptr_idx

    def is_for_same_class(self, other):
        return self._for_class is other

    def get_number_of_fields(self):
        return self._total_locations

    def with_generalized_field(self, field_idx):
        from som.vmobjects.object_with_layout import ObjectWithLayout
        if self._storage_types[field_idx] is ObjectWithLayout:
            return self
        else:
            assert self._storage_types[field_idx] is not None
            with_generalized_field = self._storage_types[:]
            with_generalized_field[field_idx] = ObjectWithLayout
            return ObjectLayout(self._total_locations, self._for_class,
                                with_generalized_field)

    def with_initialized_field(self, field_idx, spec_class):
        from som.vmobjects.object_with_layout import ObjectWithLayout
        # First we generalize to Integer, Double, or Object
        # don't need more precision
        if spec_class is Integer or spec_class is Double:
            spec_type = spec_class
        else:
            spec_type = ObjectWithLayout

        if self._storage_types[field_idx] is spec_type:
            return self
        else:
            assert self._storage_types[field_idx] is None
            with_initialized_field = self._storage_types[:]
            with_initialized_field[field_idx] = spec_type
            return ObjectLayout(self._total_locations, self._for_class,
                                with_initialized_field)

    def get_storage_location(self, field_idx):
        return self._storage_locations[field_idx]

    def get_number_of_used_extended_ptr_locations(self):
        required_ext_fields = (self._ptr_locations_used
                               - NUMBER_OF_POINTER_FIELDS)
        if required_ext_fields < 0:
            return 0
        else:
            return required_ext_fields

    def get_number_of_used_extended_prim_locations(self):
        required_ext_field = (self._prim_locations_used
                              - NUMBER_OF_PRIMITIVE_FIELDS)
        if required_ext_field < 0:
            return 0
        else:
            return required_ext_field
