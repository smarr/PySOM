from collections import OrderedDict

from som.vm.symbols import symbol_for
from som.vmobjects.array import Array
from som.vmobjects.clazz import Class


class ClassGenerationContext(object):
    def __init__(self, universe):
        self.universe = universe

        self.name = None
        self._super_class = None
        self._class_side = False  # to be overridden
        self._instance_fields = []
        self._class_fields = []

        self._instance_methods = OrderedDict()
        self._class_methods = OrderedDict()

        self._instance_has_primitives = False
        self._class_has_primitives = False

    def __str__(self):
        result = "CGenc("
        if self.name:
            result += self.name.get_embedded_string()
        result += ")"
        return result

    def get_super_class(self):
        if self._class_side:
            return self._super_class.get_class(self.universe)
        return self._super_class

    def set_super_class(self, super_class):
        self._super_class = super_class
        self._set_instance_fields_of_super(super_class.get_instance_fields())
        self._set_class_fields_of_super(
            super_class.get_class(self.universe).get_instance_fields()
        )

    def _set_instance_fields_of_super(self, field_names):
        for i in range(0, field_names.get_number_of_indexable_fields()):
            self._instance_fields.append(field_names.get_indexable_field(i))

    def _set_class_fields_of_super(self, field_names):
        for i in range(0, field_names.get_number_of_indexable_fields()):
            self._class_fields.append(field_names.get_indexable_field(i))

    def add_instance_method(self, method):
        self._instance_methods[method.get_signature()] = method
        if method.is_primitive():
            self._instance_has_primitives = True

    def switch_to_class_side(self):
        self._class_side = True

    def add_class_method(self, method):
        self._class_methods[method.get_signature()] = method
        if method.is_primitive():
            self._class_has_primitives = True

    def add_instance_field(self, field):
        self._instance_fields.append(field)

    def get_instance_field_name(self, _idx):
        return "not yet implemented"
        # TODO: return self._instance_fields[idx] and support of super classes, I think

    def add_class_field(self, field):
        self._class_fields.append(field)

    def has_field(self, field):
        return field in (
            self._class_fields if self.is_class_side() else self._instance_fields
        )

    def get_field_index(self, field):
        if self.is_class_side():
            return self._class_fields.index(field)
        return self._instance_fields.index(field)

    def is_class_side(self):
        return self._class_side

    def assemble(self):
        # build class class name
        cc_name = self.name.get_embedded_string() + " class"

        # Allocate the class of the resulting class
        result_class = Class(
            self.universe.metaclass_class.get_number_of_instance_fields(),
            self.universe.metaclass_class,
        )

        # Initialize the class of the resulting class
        result_class.set_instance_fields(Array.from_objects(self._class_fields[:]))
        result_class.set_instance_invokables(
            self._class_methods, self._class_has_primitives
        )
        result_class.set_name(symbol_for(cc_name))

        super_m_class = self._super_class.get_class(self.universe)
        result_class.set_super_class(super_m_class)

        # Allocate the resulting class
        result = Class(result_class.get_number_of_instance_fields(), result_class)

        # Initialize the resulting class
        result.set_name(self.name)
        result.set_super_class(self._super_class)
        result.set_instance_fields(Array.from_objects(self._instance_fields[:]))
        result.set_instance_invokables(
            self._instance_methods, self._instance_has_primitives
        )

        return result

    def assemble_system_class(self, system_class):
        system_class.set_instance_invokables(
            self._instance_methods, self._instance_has_primitives
        )
        system_class.set_instance_fields(Array.from_objects(self._instance_fields[:]))

        # class-bound == class-instance-bound
        super_m_class = system_class.get_class(self.universe)
        super_m_class.set_instance_invokables(
            self._class_methods, self._class_has_primitives
        )
        super_m_class.set_instance_fields(Array.from_objects(self._class_fields[:]))
