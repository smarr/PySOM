from som.primitives.false_primitives import FalsePrimitivesBase as _Base


def _or(_ivkbl, frame):
    block = frame.pop()
    frame.pop()
    block_method = block.get_method()
    block_method.invoke(frame)


FalsePrimitives = _Base

# self._install_instance_primitive(Primitive("or:", self.universe, _or))
# self._install_instance_primitive(Primitive("||", self.universe, _or))
