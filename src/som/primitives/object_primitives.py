from rlib.objectmodel import compute_identity_hash
from som.primitives.primitives import Primitives
from som.vm.current import current_universe

from som.vm.globals import trueObject, falseObject
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive


def _equals(op1, op2):
    if op1 is op2:
        return trueObject
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
    return rcvr.get_class(current_universe)


class ObjectPrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("==", self.universe, _equals))
        self._install_instance_primitive(
            UnaryPrimitive("hashcode", self.universe, _hashcode)
        )
        self._install_instance_primitive(
            BinaryPrimitive("instVarAt:", self.universe, _inst_var_at)
        )
        self._install_instance_primitive(
            TernaryPrimitive("instVarAt:put:", self.universe, _inst_var_at_put)
        )

        self._install_instance_primitive(UnaryPrimitive("halt", self.universe, _halt))
        self._install_instance_primitive(UnaryPrimitive("class", self.universe, _class))
