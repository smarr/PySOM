from som.interpreter.bc.frame import stack_pop, stack_top
from som.primitives.array_primitives import ArrayPrimitivesBase as _Base
from som.vmobjects.primitive import Primitive


def _at_put(_ivkbl, frame):
    value = stack_pop(frame)
    index = stack_pop(frame)
    rcvr = stack_top(frame)
    rcvr.set_indexable_field(index.get_embedded_integer() - 1, value)


class ArrayPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(Primitive("at:put:", self.universe, _at_put))
