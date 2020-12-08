class AbstractObject(object):

    def __init__(self):
        pass

    def get_class(self, universe):
        raise NotImplementedError("Subclasses need to implement get_class(universe).")

    def quick_add(self, from_method, frame, interpreter, bytecode_index):
        interpreter._send(from_method, frame, interpreter._add_symbol,
                          self.get_class(interpreter.get_universe()),
                          bytecode_index)

    def quick_multiply(self, from_method, frame, interpreter, bytecode_index):
        interpreter._send(from_method, frame, interpreter._multiply_symbol,
                          self.get_class(interpreter.get_universe()),
                          bytecode_index)

    def quick_subtract(self, from_method, frame, interpreter, bytecode_index):
        interpreter._send(from_method, frame, interpreter._subtract_symbol,
                          self.get_class(interpreter.get_universe()),
                          bytecode_index)

    @staticmethod
    def is_invokable():
        return False

    def __str__(self):
        from som.vm.universe import get_current
        return "a " + self.get_class(get_current()).get_name().get_embedded_string()
