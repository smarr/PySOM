from rlib.float import round_double, INFINITY
from math import cos, sin

from som.primitives.primitives import Primitives
from som.vmobjects.double import Double
from som.vmobjects.primitive   import UnaryPrimitive, BinaryPrimitive

import math


def _as_string(rcvr):
    return rcvr.prim_as_string()


def _sqrt(rcvr):
    return Double(math.sqrt(rcvr.get_embedded_double()))


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


def _less_than(left, right):
    return left.prim_less_than(right)


def _less_than_or_equal(left, right):
    return left.prim_less_than_or_equal(right)


def _greater_than(left, right):
    return left.prim_greater_than(right)


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
        self._install_instance_primitive(UnaryPrimitive("asString", self._universe, _as_string))
        self._install_instance_primitive(UnaryPrimitive("round",    self._universe, _round))
        self._install_instance_primitive(UnaryPrimitive("asInteger", self._universe, _as_integer))

        self._install_instance_primitive(UnaryPrimitive("sqrt",     self._universe, _sqrt))
        self._install_instance_primitive(BinaryPrimitive("+",        self._universe, _plus))
        self._install_instance_primitive(BinaryPrimitive("-",        self._universe, _minus))
        self._install_instance_primitive(BinaryPrimitive("*",        self._universe, _mult))
        self._install_instance_primitive(BinaryPrimitive("//",       self._universe, _double_div))
        self._install_instance_primitive(BinaryPrimitive("%",        self._universe, _mod))
        self._install_instance_primitive(BinaryPrimitive("=",        self._universe, _equals))
        self._install_instance_primitive(BinaryPrimitive("<",        self._universe, _less_than))
        self._install_instance_primitive(BinaryPrimitive("<=",       self._universe, _less_than_or_equal))
        self._install_instance_primitive(BinaryPrimitive(">",        self._universe, _greater_than))
        self._install_instance_primitive(BinaryPrimitive("<>",       self._universe, _unequals))
        self._install_instance_primitive(BinaryPrimitive("~=",       self._universe, _unequals))

        self._install_instance_primitive(UnaryPrimitive("sin", self._universe, _sin))
        self._install_instance_primitive(UnaryPrimitive("cos", self._universe, _cos))

        self._install_class_primitive(UnaryPrimitive("PositiveInfinity", self._universe, _positive_infinity))
        self._install_class_primitive(BinaryPrimitive("fromString:", self._universe, _from_string))
