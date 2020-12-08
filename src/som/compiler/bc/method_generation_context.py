from som.compiler.method_generation_context import MethodGenerationContextBase
from som.interpreter.bc.bytecodes import bytecode_length, bytecode_stack_effect,\
    bytecode_stack_effect_depends_on_send, Bytecodes
from som.vmobjects.primitive import empty_primitive
from som.vmobjects.method_bc import BcMethod


class MethodGenerationContext(MethodGenerationContextBase):

    def __init__(self, universe):
        MethodGenerationContextBase.__init__(self, universe)

        self._arguments   = []
        self._locals      = []
        self._literals    = []
        self._finished    = False
        self._bytecode    = []

    def add_argument(self, arg):
        self._arguments.append(arg)

    def assemble(self, _dummy):
        if self._primitive:
            return empty_primitive(self._signature.get_embedded_string(), self._universe)

        num_locals = len(self._locals)

        meth = BcMethod(list(self._literals), num_locals, self._compute_stack_depth(),
                        len(self._bytecode), self._signature)

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

    def add_argument_if_absent(self, arg):
        if arg in self._locals:
            return False

        self._arguments.append(arg)
        return True

    def is_finished(self):
        return self._finished

    def set_finished(self):
        self._finished = True

    def add_local(self, local):
        self._locals.append(local)

    def remove_last_bytecode(self):
        self._bytecode = self._bytecode[:-1]

    def add_literal_if_absent(self, lit):
        if lit in self._literals:
            return False

        self._literals.append(lit)
        return True

    def add_literal(self, lit):
        i = len(self._literals)

        assert i < 128
        self._literals.append(lit)

        return i

    def update_literal(self, old_val, index, new_val):
        assert self._literals[index] == old_val
        self._literals[index] = new_val

    def find_var(self, var, triplet):
        # triplet: index, context, isArgument
        if var in self._locals:
            triplet[0] = self._locals.index(var) + len(self._arguments)
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

    def add_bytecode(self, bc):
        self._bytecode.append(bc)

    def has_bytecode(self):
        return len(self._bytecode) > 0

    def find_literal_index(self, lit):
        return self._literals.index(lit)

    def get_outer(self):
        return self._outer_genc


def create_bootstrap_method(universe):
    """ Create a fake bootstrap method to simplify later frame traversal """
    bootstrap_method = BcMethod([], 0, 2, 1, universe.symbol_for("bootstrap"))

    bootstrap_method.set_bytecode(0, Bytecodes.halt)
    bootstrap_method.set_holder(universe.systemClass)
    return bootstrap_method
