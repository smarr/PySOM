from som.primitives.true_primitives import TruePrimitivesBase as _Base


# def _and(_ivkbl, frame):
#     block = stack_pop(frame)
#     stack_pop(frame)
#     block_method = block.get_method()
#     block_method.invoke(frame)


TruePrimitives = _Base

# self._install_instance_primitive(Primitive("and:", self.universe, _and))
# self._install_instance_primitive(Primitive("&&", self.universe, _and))
