from rlib import jit
from som.vm.globals import nilObject
from som.vmobjects.array import Array
from som.vmobjects.object_with_layout import Object
from som.interpreter.objectstorage.object_layout import ObjectLayout


class Class(Object):
    _immutable_fields_ = [
        "_super_class",
        "_name",
        "_instance_fields",
        "_invokables_table",
        "has_primitives",
        "_layout_for_instances?",
    ]

    def __init__(self, number_of_fields=Object.NUMBER_OF_OBJECT_FIELDS, obj_class=None):
        Object.__init__(
            self, obj_class.get_layout_for_instances() if obj_class else None
        )
        self._super_class = nilObject
        self._name = None
        self._instance_fields = None
        self._invokables_table = None
        self.has_primitives = False

        assert number_of_fields >= 0
        self._layout_for_instances = ObjectLayout(number_of_fields, self)

    def get_super_class(self):
        return self._super_class

    def set_super_class(self, value):
        self._super_class = value

    def has_super_class(self):
        return self._super_class is not nilObject

    def get_name(self):
        return self._name

    def set_name(self, value):
        self._name = value

    def get_instance_fields(self):
        return self._instance_fields

    def set_instance_fields(self, value):
        assert isinstance(value, Array)
        self._instance_fields = value
        if (
            self._layout_for_instances is None
            or value.get_number_of_indexable_fields()
            != self._layout_for_instances.get_number_of_fields()
        ):
            self._layout_for_instances = ObjectLayout(
                value.get_number_of_indexable_fields(), self
            )

    def get_instance_invokables(self):
        if not self._invokables_table:
            return Array.from_size(0)

        result = [None] * len(self._invokables_table)

        i = 0
        for invokable in self._invokables_table.values():
            result[i] = invokable
            i += 1

        return Array.from_objects(result)

    def set_instance_invokables(self, value, has_primitives):
        self.has_primitives = has_primitives

        if not value:
            assert self._invokables_table is None
            return

        self._invokables_table = value
        for i in value.values():
            i.set_holder(self)

    def get_number_of_instance_invokables(self):
        """Return the number of instance invokables in this class"""
        return len(self._invokables_table)

    def get_instance_invokables_for_disassembler(self):
        return self._invokables_table.values()

    @jit.elidable_promote("all")
    def lookup_invokable(self, signature):
        # Lookup invokable and return if found
        if self._invokables_table:
            invokable = self._invokables_table.get(signature, None)
            if invokable:
                return invokable

        # Traverse the super class chain by calling lookup on the super class
        if self.has_super_class():
            invokable = self.get_super_class().lookup_invokable(signature)
            if invokable:
                if not self._invokables_table:
                    self._invokables_table = {}
                self._invokables_table[signature] = invokable
                return invokable

        # Invokable not found
        return None

    def lookup_field_index(self, field_name):
        # Lookup field with given name in array of instance fields
        i = self.get_number_of_instance_fields() - 1
        while i >= 0:
            # Return the current index if the name matches
            if field_name == self.get_instance_field_name(i):
                return i
            i -= 1

        # Field not found
        return -1

    def add_primitive(self, value, warn_if_not_existing):
        if warn_if_not_existing and (
            not self._invokables_table
            or value.get_signature() not in self._invokables_table
        ):
            from som.vm.universe import std_print, std_println

            std_print(
                "Warning: Primitive " + value.get_signature().get_embedded_string()
            )
            std_println(
                " is not in class definition for class "
                + self.get_name().get_embedded_string()
            )

        value.set_holder(self)
        if self._invokables_table is None:
            self._invokables_table = {}
        self._invokables_table[value.get_signature()] = value

    def get_instance_field_name(self, index):
        return self.get_instance_fields().get_indexable_field(index)

    def get_layout_for_instances(self):
        return self._layout_for_instances

    def update_instance_layout_with_initialized_field(self, field_idx, spec_type):
        updated = self._layout_for_instances.with_initialized_field(
            field_idx, spec_type
        )
        if updated is not self._layout_for_instances:
            self._layout_for_instances = updated
        return self._layout_for_instances

    def update_instance_layout_with_generalized_field(self, field_idx):
        updated = self._layout_for_instances.with_generalized_field(field_idx)
        if updated is not self._layout_for_instances:
            self._layout_for_instances = updated
        return self._layout_for_instances

    @jit.elidable_promote("all")
    def get_number_of_instance_fields(self):
        # Get the total number of instance fields in this class
        return self.get_instance_fields().get_number_of_indexable_fields()

    def needs_primitives(self):
        if self.has_primitives:
            return True
        # a bit involved to make RPython's type inferencer happy
        clazz = self._object_layout.for_class
        if isinstance(clazz, Class):
            return clazz.has_primitives
        return False

    def load_primitives(self, display_warning, universe):
        from som.primitives.known import primitives_for_class, PrimitivesNotFound

        try:
            prims = primitives_for_class(self)
            prims(universe).install_primitives_in(self)
        except PrimitivesNotFound:
            if display_warning:
                from som.vm.universe import error_println

                error_println(
                    "Loading of primitives failed for %s. Currently, "
                    "we support primitives only for known classes" % self.get_name()
                )

    def __str__(self):
        return "Class(" + self.get_name().get_embedded_string() + ")"
