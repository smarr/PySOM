from som.vmobjects.object      import Object
from som.primitives.primitives import Primitives

from importlib import import_module
import inspect

class Class(Object):
    
    # Static field indices and number of class fields
    SUPER_CLASS_INDEX         = 1 + Object.CLASS_INDEX
    NAME_INDEX                = 1 + SUPER_CLASS_INDEX
    INSTANCE_FIELDS_INDEX     = 1 + NAME_INDEX
    INSTANCE_INVOKABLES_INDEX = 1 + INSTANCE_FIELDS_INDEX
    NUMBER_OF_CLASS_FIELDS    = 1 + INSTANCE_INVOKABLES_INDEX

    
    def __init__(self, universe, number_of_fields=-1):
        Object.__init__(self, universe.nilObject, number_of_fields)
        self._invokables_table = {}
        self._universe = universe
        
    def get_super_class(self):
        # Get the super class by reading the field with super class index
        return self.get_field(self.SUPER_CLASS_INDEX)

    def set_super_class(self, value):
        # Set the super class by writing to the field with super class index
        self.set_field(self.SUPER_CLASS_INDEX, value)
    
    def has_super_class(self):
        # Check whether or not this class has a super class
        return self.get_field(self.SUPER_CLASS_INDEX) != self._universe.nilObject


    def get_name(self):
        # Get the name of this class by reading the field with name index
        return self.get_field(self.NAME_INDEX)
  
    def set_name(self, value):
        # Set the name of this class by writing to the field with name index
        self.set_field(self.NAME_INDEX, value)

    def get_instance_fields(self):
        # Get the instance fields by reading the field with the instance fields index
        return self.get_field(self.INSTANCE_FIELDS_INDEX)

    def set_instance_fields(self, value):
        # Set the instance fields by writing to the field with the instance fields index
        self.set_field(self.INSTANCE_FIELDS_INDEX, value)
  
    def get_instance_invokables(self):
        # Get the instance invokables by reading the field with the instance
        # invokables index
        return self.get_field(self.INSTANCE_INVOKABLES_INDEX)

 
    def set_instance_invokables(self, value):
        # Set the instance invokables by writing to the field with the instance
        # invokables index
        self.set_field(self.INSTANCE_INVOKABLES_INDEX, value)
 
        # Make sure this class is the holder of all invokables in the array
        for i in range(0, self.get_number_of_instance_invokables()):
            invokable = self.get_instance_invokable(i)
            assert invokable is not None
            invokable.set_holder(self)
    
    def get_number_of_instance_invokables(self):
        # Return the number of instance invokables in this class
        return self.get_instance_invokables().get_number_of_indexable_fields()
  
    def get_instance_invokable(self, index):
        # Get the instance invokable with the given index
        return self.get_instance_invokables().get_indexable_field(index)
 
    def set_instance_invokable(self, index, value):
        # Set this class as the holder of the given invokable
        value.set_holder(self)
 
        # Set the instance method with the given index to the given value
        self.get_instance_invokables().set_indexable_field(index, value)
  
    def _get_default_number_of_fields(self):
        # Return the default number of fields in a class
        return self.NUMBER_OF_CLASS_FIELDS
  
    def lookup_invokable(self, signature):
        # Lookup invokable and return if found
        invokable = self._invokables_table.get(signature, None)
        if invokable:
            return invokable
 
        # Lookup invokable with given signature in array of instance invokables
        for i in range(0, self.get_number_of_instance_invokables()):
            invokable = self.get_instance_invokable(i)
            # Return the invokable if the signature matches
            if invokable.get_signature() == signature:
                self._invokables_table[signature] = invokable
                return invokable
      
        # Traverse the super class chain by calling lookup on the super class
        if self.has_super_class():
            invokable = self.get_super_class().lookup_invokable(signature)
            if invokable:
                self._invokables_table[signature] = invokable
                return invokable
 
        # Invokable not found
        return None
 
    def lookup_field_index(self, fieldName):
        # Lookup field with given name in array of instance fields
        i = self.get_number_of_instance_fields() - 1
        while i >= 0:
            # Return the current index if the name matches
            if fieldName == self.get_instance_field_name(i):
                return i
            i -= 1

        # Field not found
        return -1


    def add_instance_invokable(self, value):
        # Add the given invokable to the array of instance invokables
        for i in range(0, self.get_number_of_instance_invokables()):
            # Get the next invokable in the instance invokable array
            invokable = self.get_instance_invokable(i)
  
            # Replace the invokable with the given one if the signature matches
            if invokable.get_signature() == value.get_signature():
                self.set_instance_invokable(i, value)
                return False
  
        # Append the given method to the array of instance methods
        self.set_instance_invokables(self.get_instance_invokables().copy_and_extend_with(value, self._universe))
        return True
  
    def add_instance_primitive(self, value):
        if self.add_instance_invokable(value):
            self._universe.std_print("Warning: Primitive " + value.get_signature().get_string())
            self._universe.std_println(" is not in class definition for class " + self.get_name().get_string())
  
    def get_instance_field_name(self, index):
        # Get the name of the instance field with the given index
        if index >= self._get_number_of_super_instance_fields():
            # Adjust the index to account for fields defined in the super class
            index -= self._get_number_of_super_instance_fields()
  
            # Return the symbol representing the instance fields name
            return self.get_instance_fields().get_indexable_field(index)
        else:
            # Ask the super class to return the name of the instance field
            return self.get_super_class().get_instance_field_name(index)
 
    def get_number_of_instance_fields(self):
        # Get the total number of instance fields in this class
        return (self.get_instance_fields().get_number_of_indexable_fields() +
                self._get_number_of_super_instance_fields())

    def _get_number_of_super_instance_fields(self):
        # Get the total number of instance fields defined in super classes
        if self.has_super_class():
            return self.get_super_class().get_number_of_instance_fields()
        else:
            return 0
  
    def has_primitives(self):
        # Lookup invokable with given signature in array of instance invokables
        for i in range(0, self.get_number_of_instance_invokables()):
            # Get the next invokable in the instance invokable array
            if self.get_instance_invokable(i).is_primitive():
                return True
        
        return False
  
    def load_primitives(self):
        # determine module name for the primitives of the class
        module_name = "som.primitives." + self.get_name().get_string().lower() + "_primitives"
        
        # Try loading the primitives
        module = import_module(module_name)
        for name, element in inspect.getmembers(module):
            if (inspect.isclass(element) and 
                  issubclass(element, Primitives) and
                  element is not Primitives):
                element(self._universe).install_primitives_in(self)
  
    def replace_bytecodes(self):
        cnt = self.get_number_of_instance_invokables()
        for i in range(0, cnt):
            inv = self.get_instance_invokable(i)
            if not inv.is_primitive():
                inv.replace_bytecodes()  

    def __str__(self):
        return "Class(" + self.get_name().get_string() + ")"
