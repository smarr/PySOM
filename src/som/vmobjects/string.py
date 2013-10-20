from som.vmobjects.object import Object

class String(Object):
    
    def __init__(self, nilObject, value):
        Object.__init__(self, nilObject)
        self._string = value
    
    def get_embedded_string(self):
        return self._string
        
    def __str__(self):
        return "\"" + self._string + "\""
