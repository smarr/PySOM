from som.primitives.primitives import Primitives
from som.vm.universe import Universe
from som.vmobjects.primitive import UnaryPrimitive


def _new(rcvr):
    return Universe.new_instance(rcvr)


def _name(rcvr):
    return rcvr.get_name()


def _super_class(rcvr):
    return rcvr.get_super_class()


def _methods(rcvr):
    return rcvr.get_instance_invokables()


def _fields(rcvr):
    return rcvr.get_instance_fields()


class ClassPrimitives(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("new", _new))
        self._install_instance_primitive(UnaryPrimitive("name", _name))
        self._install_instance_primitive(UnaryPrimitive("superclass", _super_class))
        self._install_instance_primitive(UnaryPrimitive("methods", _methods))
        self._install_instance_primitive(UnaryPrimitive("fields", _fields))
