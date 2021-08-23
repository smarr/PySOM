from math import cos, sin, sqrt
from rlib.float import round_double, INFINITY

from som.primitives.primitives import Primitives
from som.vm.globals import falseObject, trueObject
from som.vmobjects.double import Double
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive


def _as_string(rcvr):
    return rcvr.prim_as_string()


def _sqrt(rcvr):
    return Double(sqrt(rcvr.get_embedded_double()))


def _plus(left, right):
    return left.prim_add(right)


def _minus(left, right):
    return left.prim_subtract(right)


def _mult(left, right):
    return left.prim_multiply(right)


def _double_div(left, right):
    return left.prim_double_div(right)


def _mod(left, right):
    return left.prim_modulo(right)


def _equals(left, right):
    return left.prim_equals(right)


def _unequals(left, right):
    return left.prim_unequals(right)


def _min(left, right):
    if left.prim_less_than(right):
        return left
    return right


def _max(left, right):
    if left.prim_less_than(right):
        return right
    return left


def _less_than(left, right):
    if left.prim_less_than(right):
        return trueObject
    return falseObject


def _less_than_or_equal(left, right):
    return left.prim_less_than_or_equal(right)


def _greater_than(left, right):
    return left.prim_greater_than(right)


def _greater_than_or_equal(left, right):
    return left.prim_greater_than_or_equal(right)


def _round(rcvr):
    from som.vmobjects.integer import Integer

    int_value = int(round_double(rcvr.get_embedded_double(), 0))
    return Integer(int_value)


def _as_integer(rcvr):
    from som.vmobjects.integer import Integer

    return Integer(int(rcvr.get_embedded_double()))


def _cos(rcvr):
    result = cos(rcvr.get_embedded_double())
    return Double(result)


def _sin(rcvr):
    result = sin(rcvr.get_embedded_double())
    return Double(result)


def _positive_infinity(_rcvr):
    return Double(INFINITY)


def _from_string(_rcvr, string):
    try:
        return Double(float(string.get_embedded_string()))
    except ValueError:
        from som.vm.globals import nilObject

        return nilObject


class DoublePrimitives(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("asString", _as_string))
        self._install_instance_primitive(UnaryPrimitive("round", _round))
        self._install_instance_primitive(UnaryPrimitive("asInteger", _as_integer))

        self._install_instance_primitive(UnaryPrimitive("sqrt", _sqrt))
        self._install_instance_primitive(BinaryPrimitive("+", _plus))
        self._install_instance_primitive(BinaryPrimitive("-", _minus))
        self._install_instance_primitive(BinaryPrimitive("*", _mult))
        self._install_instance_primitive(BinaryPrimitive("//", _double_div))
        self._install_instance_primitive(BinaryPrimitive("%", _mod))
        self._install_instance_primitive(BinaryPrimitive("=", _equals))
        self._install_instance_primitive(BinaryPrimitive("<", _less_than))
        self._install_instance_primitive(BinaryPrimitive("<=", _less_than_or_equal))
        self._install_instance_primitive(BinaryPrimitive(">", _greater_than))
        self._install_instance_primitive(BinaryPrimitive(">=", _greater_than_or_equal))
        self._install_instance_primitive(BinaryPrimitive("<>", _unequals))
        self._install_instance_primitive(BinaryPrimitive("~=", _unequals))

        self._install_instance_primitive(BinaryPrimitive("max:", _max))
        self._install_instance_primitive(BinaryPrimitive("min:", _min))

        self._install_instance_primitive(UnaryPrimitive("sin", _sin))
        self._install_instance_primitive(UnaryPrimitive("cos", _cos))

        self._install_class_primitive(
            UnaryPrimitive("PositiveInfinity", _positive_infinity)
        )
        self._install_class_primitive(BinaryPrimitive("fromString:", _from_string))
