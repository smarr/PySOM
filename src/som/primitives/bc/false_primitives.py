from som.interpreter.bc.frame import stack_pop
from som.primitives.false_primitives import FalsePrimitivesBase as _Base


def _or(_ivkbl, frame):
    block = stack_pop(frame)
    stack_pop(frame)
    block_method = block.get_method()
    block_method.invoke_n(frame)


FalsePrimitives = _Base

# self._install_instance_primitive(Primitive("or:", self.universe, _or))
# self._install_instance_primitive(Primitive("||", self.universe, _or))
