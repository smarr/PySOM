from som.primitives.true_primitives import TruePrimitivesBase as _Base


def _and(ivkbl, frame, interpreter):
    block = frame.pop()
    frame.pop()
    block_method = block.get_method()
    block_method.invoke(frame, interpreter)


TruePrimitives = _Base

# self._install_instance_primitive(Primitive("and:", self._universe, _and))
# self._install_instance_primitive(Primitive("&&", self._universe, _and))
