class Object(object):
    
    # Static field indices and number of object fields
    CLASS_INDEX             = 0
    NUMBER_OF_OBJECT_FIELDS = 1 + CLASS_INDEX

    def __init__(self, nilObject, number_of_fields = -1):
        num_fields = number_of_fields if number_of_fields != -1 else self._get_default_number_of_fields()
        self._fields = None
        self.set_number_of_fields_and_clear(num_fields, nilObject)
    
    def get_class(self):
        # Get the class of this object by reading the field with class index
        return self.get_field(self.CLASS_INDEX)

    def set_class(self, value):
        # Set the class of this object by writing to the field with class index
        self.set_field(self.CLASS_INDEX, value)

    def get_field_name(self, index):
        # Get the name of the field with the given index
        return self.get_class().get_instance_field_name(index)

    def get_field_index(self, name):
        # Get the index for the field with the given name
        return self.get_class().lookup_field_fndex(name)

    def get_number_of_fields(self):
        # Get the number of fields in this object
        return len(self._fields)

    def set_number_of_fields_and_clear(self, value, nilObject):
        # Allocate a new array of fields
        self._fields = [nilObject] * value

    def _get_default_number_of_fields(self):
        # Return the default number of fields in an object
        return self.NUMBER_OF_OBJECT_FIELDS
    
    def get_field(self, index):
        # Get the field with the given index
        return self._fields[index]
  
    def set_field(self, index, value):
        # Set the field with the given index to the given value
        self._fields[index] = value
    
    def send(self, selector_string, arguments, universe, interpreter):
        # Turn the selector string into a selector
        selector = universe.symbol_for(selector_string)

        # Push the receiver onto the stack
        interpreter.get_frame().push(self)

        # Push the arguments onto the stack
        for arg in arguments:
            interpreter.get_frame().push(arg)

        # Lookup the invokable
        invokable = self.get_class().lookup_invokable(selector)

        # Invoke the invokable
        invokable.invoke(interpreter.get_frame(), interpreter)
  

    def send_does_not_understand(self, selector, universe, interpreter):
        # Compute the number of arguments
        number_of_arguments = selector.get_number_of_signature_arguments()

        frame = interpreter.get_frame()

        # Allocate an array with enough room to hold all arguments
        arguments_array = universe.new_array_with_length(number_of_arguments)

        # Remove all arguments and put them in the freshly allocated array
        i = number_of_arguments - 1
        
        while i >= 0:
            arguments_array.set_indexable_field(i, frame.pop())
            i -= 1
            
        args = (selector, arguments_array)
        self.send("doesNotUnderstand:arguments:", args, universe, interpreter)

    def send_unknown_global(self, global_name, universe, interpreter):
        arguments = (global_name, )
        self.send("unknownGlobal:", arguments, universe, interpreter)

    def send_escaped_block(self, block, universe, interpreter):
        arguments = (block, )
        self.send("escapedBlock:", arguments, universe, interpreter)

    def __str__(self):
        return "a " + self.get_class().get_name().get_string()
