from som.primitives.primitives import Primitives
from som.vmobjects.primitive import UnaryPrimitive


def _holder(rcvr):
    return rcvr.get_holder()


def _signature(rcvr):
    return rcvr.get_signature()


class InvokablePrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("holder", _holder))
        self._install_instance_primitive(UnaryPrimitive("signature", _signature))
