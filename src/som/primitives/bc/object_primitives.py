from som.primitives.object_primitives import ObjectPrimitivesBase as _Base
from som.vm.current import current_universe

from som.vmobjects.object import Object
from som.vmobjects.primitive import (
    UnaryPrimitive,
    BinaryPrimitive,
    TernaryPrimitive,
)
from som.vmobjects.array import Array


def _object_size(rcvr):
    from som.vmobjects.integer import Integer

    size = 0

    if isinstance(rcvr, Object):
        size = rcvr.get_number_of_fields()
    elif isinstance(rcvr, Array):
        size = rcvr.get_number_of_indexable_fields()

    return Integer(size)


def _perform(rcvr, selector):
    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)
    return invokable.invoke_1(rcvr)


def _perform_in_superclass(rcvr, selector, clazz):
    invokable = clazz.lookup_invokable(selector)
    return invokable.invoke_1(rcvr)


def _perform_with_arguments(rcvr, selector, args):
    num_args = args.get_number_of_indexable_fields() + 1

    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)

    if num_args == 1:
        return invokable.invoke_1(rcvr)
    if num_args == 2:
        return invokable.invoke_2(rcvr, args.get_indexable_field(0))
    if num_args == 3:
        return invokable.invoke_3(
            rcvr, args.get_indexable_field(0), args.get_indexable_field(1)
        )
    raise Exception("Not yet implemented")
    # invokable.invoke_n(frame)


class ObjectPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(
            UnaryPrimitive("objectSize", self.universe, _object_size)
        )
        self._install_instance_primitive(
            BinaryPrimitive("perform:", self.universe, _perform)
        )
        self._install_instance_primitive(
            TernaryPrimitive(
                "perform:inSuperclass:", self.universe, _perform_in_superclass
            )
        )
        self._install_instance_primitive(
            TernaryPrimitive(
                "perform:withArguments:", self.universe, _perform_with_arguments
            )
        )
