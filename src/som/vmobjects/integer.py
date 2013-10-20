from som.vmobjects.object import Object

class Integer(Object):
    
    def __init__(self, nilObject, value):
        Object.__init__(self, nilObject)
        self._embedded_integer = value
    
    def get_embedded_integer(self):
        return self._embedded_integer
        
    def get_embedded_value(self):
        """This Method is polymorphic with BigInteger"""
        return self._embedded_integer
    
    def __str__(self):
        return str(self._embedded_integer)
    
    @classmethod
    def value_fits(cls, value):
        return value <= 2147483647 and value > -2147483646
