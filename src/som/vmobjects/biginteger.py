from som.vmobjects.object import Object

class BigInteger(Object):
    def __init__(self, nilObject):
        Object.__init__(self, nilObject)
        self._embedded_biginteger = None
    
    def get_embedded_biginteger(self):
        return self._embedded_biginteger
    
    def get_embedded_value(self):
        """This Method is polymorphic with Integer"""
        return self._embedded_biginteger
    
    def set_embedded_biginteger(self, value):
        self._embedded_biginteger = value
