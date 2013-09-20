from som.interpreter.bytecodes import bytecode_length, bytecode_stack_effect, bytecode_stack_effect_depends_on_send, Bytecodes as BC
from som.vmobjects.primitive   import Primitive, empty_primitive

class MethodGenerationContext(object):
    
    def __init__(self):
        self._holder_genc = None
        self._outer_genc  = None
        self._block_method = False
        self._signature   = None
        self._arguments   = []
        self._primitive   = False # to be changed
        self._locals      = []
        self._literals    = []
        self._finished    = False
        self._bytecode    = []

  
    def set_holder(self, cgenc):
        self._holder_genc = cgenc

    def add_argument(self, arg):
        self._arguments.append(arg)

    def is_primitive(self):
        return self._primitive
  
    def assemble_primitive(self, universe):
        return empty_primitive(self._signature.get_string(), universe)

    def assemble(self, universe):
        # create a method instance with the given number of bytecodes and literals
        num_literals = len(self._literals)

        meth = universe.new_method(self._signature, len(self._bytecode), num_literals)

        # populate the fields that are immediately available
        num_locals = len(self._locals)
        meth.set_number_of_locals(universe.new_integer(num_locals))

        meth.set_maximum_number_of_stack_elements(universe.new_integer(self._compute_stack_depth()))

        # copy literals into the method
        i = 0
        for l in self._literals:
            meth.set_indexable_field(i, l)
            i += 1
        
        # copy bytecodes into method
        i = 0
        for bc in self._bytecode:
            meth.set_bytecode(i, bc)
            i += 1
    
        # return the method - the holder field is to be set later on!
        return meth

    def _compute_stack_depth(self): 
        depth     = 0
        max_depth = 0
        i         = 0

        while i < len(self._bytecode):
            bc = self._bytecode[i]
            
            if bytecode_stack_effect_depends_on_send(bc):
                signature = self._literals[self._bytecode[i + 1]]
                depth += bytecode_stack_effect(bc, signature.get_number_of_signature_arguments())
            else:
                depth += bytecode_stack_effect(bc)
            
            i += bytecode_length(bc)
            
            if depth > max_depth:
                max_depth = depth
        
        return max_depth


    def set_primitive(self, boolean):
        self._primitive = boolean

    def set_signature(self, sig):
        self._signature = sig

    def add_argument_if_absent(self, arg):
        if arg in self._locals:
            return False
        
        self._arguments.append(arg)
        return True

    def is_finished(self):
        return self._finished

    def set_finished(self, boolean = True):
        self._finished = boolean

    def add_local_if_absent(self, local):
        if local in self._locals:
            return False
   
        self._locals.append(local)
        return True

    def add_local(self, local):
        self._locals.append(local)

    def remove_last_bytecode(self):
        self._bytecode = self._bytecode[:-1]

    def is_block_method(self):
        return self._block_method

    def add_literal_if_absent(self, lit):
        if lit in self._literals:
            return False
        
        self._literals.append(lit)
        return True

    def set_is_block_method(self, boolean):
        self._block_method = boolean

    def get_holder(self):
        return self._holder_genc
  
    def set_outer(self, mgenc):
        self._outer_genc = mgenc

    def add_literal(self, lit):
        self._literals.append(lit)

    def find_var(self, var, triplet):
        # triplet: index, context, isArgument
        if var in self._locals:
            triplet[0] = self._locals.index(var)
            return True
        
        if var in self._arguments:
            triplet[0] = self._arguments.index(var)
            triplet[2] = True
            return True
        
        if self._outer_genc:
            triplet[1] = triplet[1] + 1
            return self._outer_genc.find_var(var, triplet)
        else:
            return False

    def has_field(self, field):
        return self._holder_genc.has_field(field)

    def get_field_index(self, field):
        return self._holder_genc.get_field_index(field)

    def get_number_of_arguments(self):
        return len(self._arguments)

    def add_bytecode(self, bc):
        self._bytecode.append(bc)

    def find_literal_index(self, lit):
        return self._literals.index(lit)

    def get_outer(self):
        return self._outer_genc

    def get_signature(self):
        return self._signature
