from rlib.objectmodel import compute_identity_hash
from som.primitives.primitives import Primitives

from som.vm.globals import trueObject, falseObject
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive


def _equals(op1, op2):
    if op1 is op2:
        return trueObject
    else:
        return falseObject


def _hashcode(rcvr):
    from som.vmobjects.integer import Integer
    return Integer(compute_identity_hash(rcvr))


def _inst_var_at(rcvr, idx):
    return rcvr.get_field(idx.get_embedded_integer() - 1)


class ObjectPrimitivesBase(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("==", self._universe, _equals))
        self._install_instance_primitive(UnaryPrimitive("hashcode", self._universe, _hashcode))
        self._install_instance_primitive(
            BinaryPrimitive("instVarAt:", self._universe, _inst_var_at))
