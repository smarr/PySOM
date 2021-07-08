from som.primitives.object_primitives import ObjectPrimitivesBase as _Base
from som.vmobjects.integer import Integer

from som.vmobjects.object_with_layout import ObjectWithLayout
from som.vmobjects.primitive import (
    BinaryPrimitive,
    UnaryPrimitive,
)
from som.vmobjects.array import Array


def _object_size(rcvr):
    size = 0

    if isinstance(rcvr, ObjectWithLayout):
        size = rcvr.get_number_of_fields()
    elif isinstance(rcvr, Array):
        size = rcvr.get_number_of_indexable_fields()

    return Integer(size)


def _inst_var_named(rcvr, arg):
    i = rcvr.get_field_index(arg)
    return rcvr.get_field(i)


class ObjectPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(
            UnaryPrimitive("objectSize", self.universe, _object_size)
        )
        self._install_instance_primitive(
            BinaryPrimitive("instVarNamed:", self.universe, _inst_var_named)
        )
