from som.vmobjects.array import Array
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive
from som.primitives.primitives import Primitives


def _at(rcvr, i):
    return rcvr.get_indexable_field(i.get_embedded_integer() - 1)


def _at_put(rcvr, index, value):
    rcvr.set_indexable_field(index.get_embedded_integer() - 1, value)
    return rcvr


def _length(rcvr):
    from som.vmobjects.integer import Integer

    return Integer(rcvr.get_number_of_indexable_fields())


def _copy(rcvr):
    return rcvr.copy()


def _new(_rcvr, length):
    return Array.from_size(length.get_embedded_integer())


class ArrayPrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("at:", self.universe, _at))
        self._install_instance_primitive(
            TernaryPrimitive("at:put:", self.universe, _at_put)
        )
        self._install_instance_primitive(
            UnaryPrimitive("length", self.universe, _length)
        )
        self._install_instance_primitive(UnaryPrimitive("copy", self.universe, _copy))

        self._install_class_primitive(BinaryPrimitive("new:", self.universe, _new))
