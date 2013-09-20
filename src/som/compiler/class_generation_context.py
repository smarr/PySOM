class ClassGenerationContext(object):
    
    def __init__(self, universe):
        self._universe = universe

        self._name       = None
        self._super_name = None
        self._class_side = False # to be overridden
        self._number_of_instance_fields_of_super = -1
        self._number_of_class_fields_of_super = -1
        self._instance_fields  = []
        self._instance_methods = []
        self._class_fields     = []
        self._class_methods    = []

    def set_name(self, symbol):
        self._name = symbol

    def set_super_name(self, symbol):
        self._super_name = symbol
  

    def set_number_of_instance_fields_of_super(self, num):
        self._number_of_instance_fields_of_super = num

    def set_number_of_class_fields_of_super(self, num):
        self._number_of_class_fields_of_super = num

    def add_instance_method(self, meth):
        self._instance_methods.append(meth)


    def set_class_side(self, boolean):
        self._class_side = boolean

    def add_class_method(self, meth):
        self._class_methods.append(meth)

    def add_instance_field(self, field):
        self._instance_fields.append(field)

    def add_class_field(self, field):
        self._class_fields.append(field)

    def has_field(self, field):
        return field in (self._class_fields if self.is_class_side() else self._instance_fields)

    def get_field_index(self, field):
        local_index = (self._class_fields if self.is_class_side() else self._instance_fields).index(field)
        return (local_index +
                 (self._number_of_class_fields_of_super if self.is_class_side() else self._number_of_instance_fields_of_super))

    def is_class_side(self):
        return self._class_side

    def assemble(self):
        # build class class name
        ccname = self._name.get_string() + " class"

        # Load the super class
        super_class = self._universe.load_class(self._super_name)

        # Allocate the class of the resulting class
        result_class = self._universe.new_class(self._universe.metaclassClass)

        # Initialize the class of the resulting class
        result_class.set_instance_fields(self._universe.new_array_from_list(self._class_fields))
        result_class.set_instance_invokables(self._universe.new_array_from_list(self._class_methods))
        result_class.set_name(self._universe.symbol_for(ccname))

        super_mclass = super_class.get_class()
        result_class.set_super_class(super_mclass)

        # Allocate the resulting class
        result = self._universe.new_class(result_class)

        # Initialize the resulting class
        result.set_name(self._name)
        result.set_super_class(super_class)
        result.set_instance_fields(self._universe.new_array_from_list(self._instance_fields))
        result.set_instance_invokables(self._universe.new_array_from_list(self._instance_methods))

        return result

    def assemble_system_class(self, system_class):
        system_class.set_instance_invokables(self._universe.new_array_from_list(self._instance_methods))
        system_class.set_instance_fields(self._universe.new_array_from_list(self._instance_fields))
    
        # class-bound == class-instance-bound
        super_mclass = system_class.get_class()
        super_mclass.set_instance_invokables(self._universe.new_array_from_list(self._class_methods))
        super_mclass.set_instance_fields(self._universe.new_array_from_list(self._class_fields))
