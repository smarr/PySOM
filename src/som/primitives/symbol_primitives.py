from som.primitives.primitives import Primitives
from som.vmobjects.primitive   import BinaryPrimitive, UnaryPrimitive
from som.vm.globals import trueObject, falseObject
from som.vmobjects.string import String


def _as_string(rcvr):
    return String(rcvr.get_embedded_string())


def _equals(op1, op2):
    if op1 is op2:
        return trueObject
    else:
        return falseObject


class SymbolPrimitivesBase(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("asString", self._universe, _as_string))
        self._install_instance_primitive(BinaryPrimitive("=", self._universe, _equals), False)
