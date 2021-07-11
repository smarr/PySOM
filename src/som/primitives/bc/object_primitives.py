from som.primitives.object_primitives import ObjectPrimitivesBase as _Base

from som.vmobjects.object_with_layout import ObjectWithLayout
from som.vmobjects.primitive import (
    UnaryPrimitive,
)
from som.vmobjects.array import Array


def _object_size(rcvr):
    from som.vmobjects.integer import Integer

    size = 0

    if isinstance(rcvr, ObjectWithLayout):
        size = rcvr.get_number_of_fields()
    elif isinstance(rcvr, Array):
        size = rcvr.get_number_of_indexable_fields()

    return Integer(size)


class ObjectPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(
            UnaryPrimitive("objectSize", self.universe, _object_size)
        )
