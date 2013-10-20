from som.vmobjects.object    import Object
from som.vmobjects.primitive import Primitive

class Block(Object):
    
    NUMBER_OF_BLOCK_FIELDS = Object.NUMBER_OF_OBJECT_FIELDS
    
    def __init__(self, nilObject, method, context):
        Object.__init__(self, nilObject)
        self._number_of_arguments = 0
        self._method  = method
        self._context = context
        
    def get_method(self):
        # Get the method of this block by reading the field with method index
        return self._method
    
    def get_context(self):
        # Get the context of this block by reading the field with context index
        return self._context

    def _get_default_number_of_fields(self):
        # Return the default number of fields for a block
        return self.NUMBER_OF_BLOCK_FIELDS
  
    class Evaluation(Primitive):
        def __init__(self, num_args, universe):            
            def _invoke(ivkbl, frame, interpreter):
                # Get the block (the receiver) from the stack
                rcvr = frame.get_stack_element(ivkbl._number_of_arguments - 1)
    
                # Get the context of the block...
                context = rcvr.get_context()
    
                # Push a new frame and set its context to be the one specified in
                # the block
                new_frame = interpreter.push_new_frame(rcvr.get_method(), context)
                new_frame.copy_arguments_from(frame)
            
            Primitive.__init__(self, self._compute_signature_string(num_args), universe, _invoke)
            self._number_of_arguments = num_args

        def _compute_signature_string(self, num_args):
            # Compute the signature string
            signature_string = "value"
            if num_args > 1:
                signature_string += ":"
                if num_args > 2:
                    # Add extra with: selector elements if necessary
                    signature_string += "with:" * (num_args - 2)
          
            # Return the signature string
            return signature_string

    @classmethod
    def get_evaluation_primitive(cls, num_args, universe):
        return cls.Evaluation(num_args, universe)
