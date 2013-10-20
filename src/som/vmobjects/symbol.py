from som.vmobjects.object import Object

class Symbol(Object):
    
    def __init__(self, nilObject, value):
        Object.__init__(self, nilObject)
        self._string = value
        self._number_of_signature_arguments = self._determine_number_of_signature_arguments() # updated later
    
    def get_string(self):
        # Get the string associated to this symbol
        return self._string

    def _determine_number_of_signature_arguments(self):
        # Check for binary signature
        if self.is_binary_signature():
            return 2
        else:
            # Count the colons in the signature string
            number_of_colons = 0

            # Iterate through every character in the signature string
            for c in self._string:
                if c == ':':
                    number_of_colons += 1
            
            # The number of arguments is equal to the number of colons plus one
            return number_of_colons + 1

    def get_number_of_signature_arguments(self):
        return self._number_of_signature_arguments

    def is_binary_signature(self):
        # Check the individual characters of the string
        for c in self._string:
            if (c != '~' and c != '&' and c != '|' and c != '*' and c != '/' and
                c != '@' and c != '+' and c != '-' and c != '=' and c != '>' and
                c != '<' and c != ',' and c != '%' and c != '\\'):
                return False
        return True

    def __str__(self):
        return "#" + self._string
