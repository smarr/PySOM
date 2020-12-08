from som.vmobjects.string import String


class Symbol(String):
    _immutable_fields_ = ["_string", "_number_of_signature_arguments"]

    def __init__(self, value):
        String.__init__(self, value)
        self._number_of_signature_arguments =\
            self._determine_number_of_signature_arguments()  # updated later

    def _determine_number_of_signature_arguments(self):
        # Check for binary signature
        if self._is_binary_signature():
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

    def _is_binary_signature(self):
        # Check the individual characters of the string
        for c in self._string:
            if (c != '~' and c != '&' and c != '|' and c != '*' and c != '/' and
                c != '@' and c != '+' and c != '-' and c != '=' and c != '>' and
                c != '<' and c != ',' and c != '%' and c != '\\'):
                return False
        return True

    def __str__(self):
        return "#" + self._string

    def get_class(self, universe):
        return universe.symbolClass
