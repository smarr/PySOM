from som.vmobjects.object import Object

class Double(Object):
    
    def __init__(self, nilObject):
        super(Double, self).__init__(nilObject)
        self._embedded_double = 0.0
    
    def get_embedded_double(self):
        return self._embedded_double
    
    def set_embedded_double(self, value):
        self._embedded_double = value
