from som.primitives.false_primitives import FalsePrimitivesBase as _Base


def _or(ivkbl, rcvr, args):
    block = args[0]
    block_method = block.get_method()
    return block_method.invoke(block, [])


FalsePrimitives = _Base

# self._install_instance_primitive(Primitive("or:", self._universe, _or))
# self._install_instance_primitive(Primitive("||", self._universe, _or))
