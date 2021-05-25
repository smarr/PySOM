from som.primitives.object_primitives import ObjectPrimitivesBase as _Base
from som.vmobjects.integer import Integer

from som.vmobjects.object_with_layout import ObjectWithLayout
from som.vmobjects.primitive import Primitive, TernaryPrimitive, BinaryPrimitive, UnaryPrimitive
from som.vmobjects.array_strategy import Array


def _object_size(rcvr):
    size = 0

    if isinstance(rcvr, ObjectWithLayout):
        size = rcvr.get_number_of_fields()
    elif isinstance(rcvr, Array):
        size = rcvr.get_number_of_indexable_fields()

    return Integer(size)


def _perform(ivkbl, rcvr, args):
    selector = args[0]

    invokable = rcvr.get_class(ivkbl.get_universe()).lookup_invokable(selector)
    return invokable.invoke(rcvr, [])


def _perform_in_superclass(rcvr, selector, clazz):
    invokable = clazz.lookup_invokable(selector)
    return invokable.invoke(rcvr, [])


def _perform_with_arguments(ivkbl, rcvr, arguments):
    arg_arr  = arguments[1].as_argument_array()
    selector = arguments[0]

    invokable = rcvr.get_class(ivkbl.get_universe()).lookup_invokable(selector)
    return invokable.invoke(rcvr, arg_arr)


def _inst_var_named(rcvr, arg):
    i = rcvr.get_field_index(arg)
    return rcvr.get_field(i)


class ObjectPrimitives(_Base):

    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(UnaryPrimitive("objectSize", self._universe, _object_size))
        self._install_instance_primitive(Primitive("perform:", self._universe, _perform))
        self._install_instance_primitive(
            TernaryPrimitive("perform:inSuperclass:", self._universe, _perform_in_superclass))
        self._install_instance_primitive(
            Primitive("perform:withArguments:", self._universe, _perform_with_arguments))

        self._install_instance_primitive(
            BinaryPrimitive("instVarNamed:",  self._universe, _inst_var_named))
