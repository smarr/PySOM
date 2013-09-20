from som.vmobjects.object    import Object
from som.vmobjects.invokable import Invokable

import types

class Primitive(Object, Invokable):
    
    # Static field indices and number of primitive fields
    SIGNATURE_INDEX            = 1 + Object.CLASS_INDEX
    HOLDER_INDEX               = 1 + SIGNATURE_INDEX
    NUMBER_OF_PRIMITIVE_FIELDS = 1 + HOLDER_INDEX
    
    def __init__(self, signature_string, universe, invoke, is_empty=False):
        Object.__init__(self, universe.nilObject)
        
        # Set the class of this primitive to be the universal primitive class
        self.set_class(universe.primitiveClass)

        # Set the signature of this primitive
        self._set_signature(universe.symbol_for(signature_string))
        
        self._invoke = invoke
        #self.invoke = types.MethodType(invoke, self)

        self._is_empty = is_empty

    def invoke(self, frame, interpreter):
        inv = self._invoke
        inv(self, frame, interpreter)

    def is_primitive(self):
        return True

    def get_signature(self):
        # Get the signature by reading the field with signature index
        return self.get_field(self.SIGNATURE_INDEX)

    def _set_signature(self, value):
        # Set the signature by writing to the field with signature index
        self.set_field(self.SIGNATURE_INDEX, value)


    def get_holder(self):
        # Get the holder of this method by reading the field with holder index
        return self.get_field(self.HOLDER_INDEX)

    def set_holder(self, value):
        # Set the holder of this method by writing to the field with holder index
        self.set_field(self.HOLDER_INDEX, value)

    def _get_default_number_of_fields(self):
        # Return the default number of fields for a primitive
        return self.NUMBER_OF_PRIMITIVE_FIELDS

    def is_empty(self):
        # By default a primitive is not empty
        return self._is_empty

def empty_primitive(signature_string, universe):
    # Return an empty primitive with the given signature
    return Primitive(signature_string, universe, _invoke, True)

def _invoke(ivkbl, frame, interpreter):
    # Write a warning to the screen
    print "Warning: undefined primitive", ivkbl.get_signature().get_string(), " called"
