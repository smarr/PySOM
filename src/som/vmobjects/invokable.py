# An 'interface', or common super class for methods and primitives. 
class Invokable(object):

    _mixin_ = True

    # Tells whether this is a primitive
    def is_primitive(self):
        raise NotImplementedError()

    # Invoke this invokable object in a given frame
    def invoke(self, frame, interpreter):
        raise NotImplementedError()

    # Get the signature for this invokable object
    def get_signature(self):
        raise NotImplementedError()

    # Get the holder for this invokable object
    def get_holder(self):
        raise NotImplementedError()

    # Set the holder for this invokable object
    def set_holder(self, value):
        raise NotImplementedError()
