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


def _perform(rcvr, selector):
    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)
    return invokable.invoke_1(rcvr)


def _perform_in_superclass(rcvr, selector, clazz):
    invokable = clazz.lookup_invokable(selector)
    return invokable.invoke_1(rcvr)


def _perform_with_arguments(rcvr, selector, args):
    num_args = args.get_number_of_indexable_fields() + 1

    invokable = rcvr.get_class(current_universe).lookup_invokable(selector)

    if num_args == 1:
        return invokable.invoke_1(rcvr)
    if num_args == 2:
        return invokable.invoke_2(rcvr, args.get_indexable_field(0))
    if num_args == 3:
        return invokable.invoke_3(
            rcvr, args.get_indexable_field(0), args.get_indexable_field(1)
        )
    raise Exception("Not yet implemented")


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

        self._install_instance_primitive(
            BinaryPrimitive("perform:", self.universe, _perform)
        )
        self._install_instance_primitive(
            TernaryPrimitive(
                "perform:inSuperclass:", self.universe, _perform_in_superclass
            )
        )
        self._install_instance_primitive(
            TernaryPrimitive(
                "perform:withArguments:", self.universe, _perform_with_arguments
            )
        )
