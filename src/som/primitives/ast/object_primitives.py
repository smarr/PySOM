from som.primitives.object_primitives import ObjectPrimitivesBase as _Base
from som.vm.current import current_universe
from som.vmobjects.integer import Integer

from som.vmobjects.object_with_layout import ObjectWithLayout
from som.vmobjects.primitive import (
    Primitive,
    TernaryPrimitive,
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


def _perform(_ivkbl, rcvr, args):
    selector = args[0]

    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)
    return invokable.invoke(rcvr, [])


def _perform_in_superclass(rcvr, selector, clazz):
    invokable = clazz.lookup_invokable(selector)
    return invokable.invoke(rcvr, [])


def _perform_with_arguments(_ivkbl, rcvr, arguments):
    arg_arr = arguments[1].as_argument_array()
    selector = arguments[0]

    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)
    return invokable.invoke(rcvr, arg_arr)


def _inst_var_named(rcvr, arg):
    i = rcvr.get_field_index(arg)
    return rcvr.get_field(i)


class ObjectPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(
            UnaryPrimitive("objectSize", self.universe, _object_size)
        )
        self._install_instance_primitive(Primitive("perform:", self.universe, _perform))
        self._install_instance_primitive(
            TernaryPrimitive(
                "perform:inSuperclass:", self.universe, _perform_in_superclass
            )
        )
        self._install_instance_primitive(
            Primitive("perform:withArguments:", self.universe, _perform_with_arguments)
        )

        self._install_instance_primitive(
            BinaryPrimitive("instVarNamed:", self.universe, _inst_var_named)
        )