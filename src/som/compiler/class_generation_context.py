class ClassGenerationContext(object):

    def __init__(self, universe):
        self._universe = universe

        self._name       = None
        self._super_name = None
        self._class_side = False  # to be overridden
        self._instance_fields  = []
        self._instance_methods = []
        self._class_fields     = []
        self._class_methods    = []

    def get_name(self):
        return self._name

    def set_name(self, symbol):
        self._name = symbol

    def set_super_name(self, symbol):
        self._super_name = symbol

    def set_instance_fields_of_super(self, field_names):
        for i in range(0, field_names.get_number_of_indexable_fields()):
            self._instance_fields.append(field_names.get_indexable_field(i))

    def set_class_fields_of_super(self, field_names):
        for i in range(0, field_names.get_number_of_indexable_fields()):
            self._class_fields.append(field_names.get_indexable_field(i))

    def add_instance_method(self, method):
        self._instance_methods.append(method)

    def set_class_side(self, boolean):
        self._class_side = boolean

    def add_class_method(self, method):
        self._class_methods.append(method)

    def add_instance_field(self, field):
        self._instance_fields.append(field)

    def add_class_field(self, field):
        self._class_fields.append(field)

    def has_field(self, field):
        return field in (self._class_fields if self.is_class_side()
                         else self._instance_fields)

    def get_field_index(self, field):
        if self.is_class_side():
            return self._class_fields.index(field)
        else:
            return self._instance_fields.index(field)

    def is_class_side(self):
        return self._class_side

    def assemble(self):
        # build class class name
        cc_name = self._name.get_embedded_string() + " class"

        # Load the super class
        super_class = self._universe.load_class(self._super_name)

        # Allocate the class of the resulting class
        result_class = self._universe.new_class(self._universe.metaclassClass)

        # Initialize the class of the resulting class
        result_class.set_instance_fields(self._universe.new_array_from_list(
            self._class_fields[:]))
        result_class.set_instance_invokables(self._universe.new_array_from_list(
            self._class_methods[:]))
        result_class.set_name(self._universe.symbol_for(cc_name))

        super_m_class = super_class.get_class(self._universe)
        result_class.set_super_class(super_m_class)

        # Allocate the resulting class
        result = self._universe.new_class(result_class)

        # Initialize the resulting class
        result.set_name(self._name)
        result.set_super_class(super_class)
        result.set_instance_fields(self._universe.new_array_from_list(
            self._instance_fields[:]))
        result.set_instance_invokables(self._universe.new_array_from_list(
            self._instance_methods[:]))

        return result

    def assemble_system_class(self, system_class):
        system_class.set_instance_invokables(
            self._universe.new_array_from_list(self._instance_methods[:]))
        system_class.set_instance_fields(
            self._universe.new_array_from_list(self._instance_fields[:]))

        # class-bound == class-instance-bound
        super_m_class = system_class.get_class(self._universe)
        super_m_class.set_instance_invokables(
            self._universe.new_array_from_list(self._class_methods[:]))
        super_m_class.set_instance_fields(
            self._universe.new_array_from_list(self._class_fields[:]))
