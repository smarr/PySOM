from som.vmobjects.object import Object

class Array(Object):
    
    def __init__(self, nilObject, number_of_indexable_fields):
        Object.__init__(self, nilObject)
        
        # Private array of indexable fields
        self._indexable_fields = [nilObject] * number_of_indexable_fields
        
    def get_indexable_field(self, index):
        # Get the indexable field with the given index
        return self._indexable_fields[index]
  
    def set_indexable_field(self, index, value):
        # Set the indexable field with the given index to the given value
        self._indexable_fields[index] = value

    def get_number_of_indexable_fields(self):
        # Get the number of indexable fields in this array
        return len(self._indexable_fields)

    def copy_and_extend_with(self, value, universe):
        # Allocate a new array which has one indexable field more than this
        # array
        result = universe.new_array_with_length(
                            self.get_number_of_indexable_fields() + 1)

        # Copy the indexable fields from this array to the new array
        self._copy_indexable_fields_to(result)

        # Insert the given object as the last indexable field in the new array
        result.set_indexable_field(self.get_number_of_indexable_fields(), value)

        # Return the new array
        return result

    def _copy_indexable_fields_to(self, destination):
        # Copy all indexable fields from this array to the destination array
        for i in range(self.get_number_of_indexable_fields()):
            destination.set_indexable_field(i, self.get_indexable_field(i))
