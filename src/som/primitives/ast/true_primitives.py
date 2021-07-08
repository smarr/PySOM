from som.primitives.true_primitives import TruePrimitivesBase as _Base


def _and(_ivkbl, _rcvr, args):
    block = args[0]
    block_method = block.get_method()
    return block_method.invoke_1(block)


TruePrimitives = _Base

# self._install_instance_primitive(Primitive("and:", self.universe, _and))
# self._install_instance_primitive(Primitive("&&", self.universe, _and))
