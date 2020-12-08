from rlib.objectmodel import compute_identity_hash
from som.primitives.primitives import Primitives

from som.vm.globals import trueObject, falseObject
from som.vm.universe import get_current
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive


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


def _inst_var_at_put(rcvr, idx, val):
    rcvr.set_field(idx.get_embedded_integer() - 1, val)
    return val


def _halt(rcvr):
    # noop
    print("BREAKPOINT")
    return rcvr


def _class(rcvr):
    return rcvr.get_class(get_current())


class ObjectPrimitivesBase(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("==", self._universe, _equals))
        self._install_instance_primitive(UnaryPrimitive("hashcode", self._universe, _hashcode))
        self._install_instance_primitive(
            BinaryPrimitive("instVarAt:", self._universe, _inst_var_at))
        self._install_instance_primitive(
            TernaryPrimitive("instVarAt:put:", self._universe, _inst_var_at_put))

        self._install_instance_primitive(UnaryPrimitive("halt", self._universe, _halt))
        self._install_instance_primitive(UnaryPrimitive("class", self._universe, _class))
