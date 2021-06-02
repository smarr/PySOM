from som.primitives.object_primitives import ObjectPrimitivesBase as _Base
from som.vm.current import current_universe

from som.vmobjects.object    import Object
from som.vmobjects.primitive import Primitive, UnaryPrimitive
from som.vmobjects.array     import Array


def _object_size(rcvr):
    from som.vmobjects.integer import Integer
    size = 0

    if isinstance(rcvr, Object):
        size = rcvr.get_number_of_fields()
    elif isinstance(rcvr, Array):
        size = rcvr.get_number_of_indexable_fields()

    return Integer(size)


def _perform(ivkbl, frame):
    selector = frame.pop()
    rcvr     = frame.top()

    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)
    invokable.invoke(frame)


def _perform_in_superclass(ivkbl, frame):
    clazz    = frame.pop()
    selector = frame.pop()
    # rcvr     = frame.top()

    invokable = clazz.lookup_invokable(selector)
    invokable.invoke(frame)


def _perform_with_arguments(ivkbl, frame):
    args     = frame.pop()
    selector = frame.pop()
    rcvr     = frame.top()

    for i in range(0, args.get_number_of_indexable_fields()):
        frame.push(args.get_indexable_field(i))

    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)
    invokable.invoke(frame)


class ObjectPrimitives(_Base):

    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(UnaryPrimitive("objectSize", self.universe, _object_size))
        self._install_instance_primitive(Primitive("perform:", self.universe, _perform))
        self._install_instance_primitive(
            Primitive("perform:inSuperclass:", self.universe, _perform_in_superclass))
        self._install_instance_primitive(
            Primitive("perform:withArguments:", self.universe, _perform_with_arguments))
