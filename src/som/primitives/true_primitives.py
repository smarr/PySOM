from som.primitives.primitives import Primitives
from som.vm.globals import trueObject, falseObject
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive


def _not(_rcvr):
    return falseObject


def _or(_rcvr, _arg):
    return trueObject


class TruePrimitivesBase(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("not", self._universe, _not))
        self._install_instance_primitive(BinaryPrimitive("or:", self._universe, _or))
        self._install_instance_primitive(BinaryPrimitive("||", self._universe, _or))
