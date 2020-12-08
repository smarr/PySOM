from som.primitives.true_primitives import TruePrimitivesBase as _Base


def _and(ivkbl, rcvr, args):
    block = args[0]
    block_method = block.get_method()
    return block_method.invoke(block, [])


TruePrimitives = _Base

# self._install_instance_primitive(Primitive("and:", self._universe, _and))
# self._install_instance_primitive(Primitive("&&", self._universe, _and))
