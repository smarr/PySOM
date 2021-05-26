from rlib.arithmetic import ovfcheck, LONG_BIT, bigint_from_int
from rlib.llop import as_32_bit_unsigned_value, unsigned_right_shift

from som.primitives.primitives import Primitives
from som.vm.globals import nilObject, falseObject
from som.vmobjects.array import Array
from som.vmobjects.biginteger import BigInteger
from som.vmobjects.double      import Double
from som.vmobjects.integer     import Integer
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive
from som.vmobjects.string      import String

import math


def _as_string(rcvr):
    return rcvr.prim_as_string()


def _as_double(rcvr):
    return rcvr.prim_as_double()


def _as_32_bit_signed_value(rcvr):
    return rcvr.prim_as_32_bit_signed_value()


def _as_32_bit_unsigned_value(rcvr):
    val = as_32_bit_unsigned_value(rcvr.get_embedded_integer())
    return Integer(val)


def _sqrt(rcvr):
    assert isinstance(rcvr, Integer)
    res = math.sqrt(rcvr.get_embedded_integer())
    if res == float(int(res)):
        return Integer(int(res))
    else:
        return Double(res)


def _plus(left, right):
    return left.prim_add(right)


def _minus(left, right):
    return left.prim_subtract(right)


def _multiply(left, right):
    return left.prim_multiply(right)


def _double_div(left, right):
    return left.prim_double_div(right)


def _int_div(left, right):
    return left.prim_int_div(right)


def _mod(left, right):
    return left.prim_modulo(right)


def _remainder(left, right):
    return left.prim_remainder(right)


def _and(left, right):
    return left.prim_and(right)


def _equals_equals(left, right):
    if isinstance(right, Integer) or isinstance(right, BigInteger):
        return left.prim_equals(right)
    else:
        return falseObject


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


def _left_shift(left, right):
    assert isinstance(right, Integer)

    left_val = left.get_embedded_integer()
    right_val = right.get_embedded_integer()

    assert isinstance(left_val, int)
    assert isinstance(right_val, int)

    try:
        if not (left_val == 0 or 0 <= right_val < LONG_BIT):
            raise OverflowError
        result = ovfcheck(left_val << right_val)
        return Integer(result)
    except OverflowError:
        from som.vmobjects.biginteger import BigInteger
        return BigInteger(
            bigint_from_int(left_val).lshift(right_val))


def _unsigned_right_shift(left, right):
    assert isinstance(right, Integer)

    left_val = left.get_embedded_integer()
    right_val = right.get_embedded_integer()

    return Integer(unsigned_right_shift(left_val, right_val))


def _bit_xor(left, right):
    assert isinstance(right, Integer)
    result = left.get_embedded_integer() ^ right.get_embedded_integer()
    return Integer(result)


def _abs(rcvr):
    return rcvr.prim_abs()


def _max(left, right):
    return left.prim_max(right)


def _to(rcvr, arg):
    assert isinstance(rcvr, Integer)
    assert isinstance(arg, Integer)
    return Array.from_integers(range(rcvr.get_embedded_integer(), arg.get_embedded_integer() + 1))


def _from_string(rcvr, param):
    if not isinstance(param, String):
        return nilObject

    int_value = int(param.get_embedded_string())
    return Integer(int_value)


class IntegerPrimitivesBase(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("asString", self._universe, _as_string))
        self._install_instance_primitive(UnaryPrimitive("asDouble", self._universe, _as_double))
        self._install_instance_primitive(
            UnaryPrimitive("as32BitSignedValue", self._universe, _as_32_bit_signed_value))
        self._install_instance_primitive(
            UnaryPrimitive("as32BitUnsignedValue", self._universe, _as_32_bit_unsigned_value))

        self._install_instance_primitive(UnaryPrimitive("sqrt", self._universe, _sqrt))

        self._install_instance_primitive(BinaryPrimitive("+",  self._universe, _plus))
        self._install_instance_primitive(BinaryPrimitive("-",  self._universe, _minus))

        self._install_instance_primitive(BinaryPrimitive("*",  self._universe, _multiply))
        self._install_instance_primitive(BinaryPrimitive("//", self._universe, _double_div))
        self._install_instance_primitive(BinaryPrimitive("/",  self._universe, _int_div))
        self._install_instance_primitive(BinaryPrimitive("%",  self._universe, _mod))
        self._install_instance_primitive(BinaryPrimitive("rem:", self._universe, _remainder))
        self._install_instance_primitive(BinaryPrimitive("&",  self._universe, _and))

        self._install_instance_primitive(BinaryPrimitive("==",  self._universe, _equals_equals))

        self._install_instance_primitive(BinaryPrimitive("=",  self._universe, _equals))
        self._install_instance_primitive(BinaryPrimitive("<",  self._universe, _less_than))
        self._install_instance_primitive(BinaryPrimitive("<=", self._universe, _less_than_or_equal))
        self._install_instance_primitive(BinaryPrimitive(">",  self._universe, _greater_than))
        self._install_instance_primitive(BinaryPrimitive("<>", self._universe, _unequals))
        self._install_instance_primitive(BinaryPrimitive("~=", self._universe, _unequals))

        self._install_instance_primitive(BinaryPrimitive("<<", self._universe, _left_shift))
        self._install_instance_primitive(BinaryPrimitive("bitXor:", self._universe, _bit_xor))
        self._install_instance_primitive(
            BinaryPrimitive(">>>", self._universe, _unsigned_right_shift))
        self._install_instance_primitive(UnaryPrimitive("abs", self._universe, _abs))
        self._install_instance_primitive(BinaryPrimitive("max:", self._universe, _max))

        self._install_instance_primitive(BinaryPrimitive("to:", self._universe, _to))

        self._install_class_primitive(BinaryPrimitive("fromString:", self._universe, _from_string))
