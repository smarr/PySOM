from math import fmod
from rlib.float import float_to_str
from som.vm.globals import trueObject, falseObject
from som.vmobjects.abstract_object import AbstractObject


class Double(AbstractObject):
    _immutable_fields_ = ["_embedded_double"]

    def __init__(self, value):
        AbstractObject.__init__(self)
        assert isinstance(value, float)
        self._embedded_double = value

    def get_embedded_double(self):
        return self._embedded_double

    def __str__(self):
        return str(self._embedded_double)

    def get_class(self, universe):
        return universe.double_class

    def get_object_layout(self, universe):
        return universe.double_layout

    @staticmethod
    def _get_float(obj):
        from som.vmobjects.integer import Integer
        from som.vmobjects.biginteger import BigInteger

        if isinstance(obj, Double):
            return obj.get_embedded_double()
        if isinstance(obj, Integer):
            return float(obj.get_embedded_integer())
        if isinstance(obj, BigInteger):
            return obj.get_embedded_biginteger().tofloat()
        raise ValueError("Cannot coerce %s to Double!" % obj)

    def prim_multiply(self, right):
        r = self._get_float(right)
        return Double(self._embedded_double * r)

    def prim_inc(self):
        return Double(self._embedded_double + 1.0)

    def prim_dec(self):
        return Double(self._embedded_double - 1.0)

    def prim_add(self, right):
        r = self._get_float(right)
        return Double(self._embedded_double + r)

    def prim_bit_xor(self, right):
        raise NotImplementedError("bit operations on Double are not supported.")

    def prim_as_string(self):
        from som.vmobjects.string import String

        s = float_to_str(self._embedded_double)
        return String(s)

    def prim_subtract(self, right):
        r = self._get_float(right)
        return Double(self._embedded_double - r)

    def prim_double_div(self, right):
        r = self._get_float(right)
        return Double(self._embedded_double / r)

    def prim_int_div(self, right):
        from som.vmobjects.integer import Integer

        r = self._get_float(right)
        return Integer(int(self._embedded_double / r))

    def prim_modulo(self, right):
        r = self._get_float(right)
        return Double(fmod(self._embedded_double, r))

    def prim_remainder(self, right):
        r = self._get_float(right)
        return Double(fmod(self._embedded_double, r))

    def prim_and(self, right):
        raise NotImplementedError("bit operations on Double are not supported.")

    def prim_equals(self, right):
        r = self._get_float(right)
        if self._embedded_double == r:
            return trueObject
        return falseObject

    def prim_unequals(self, right):
        r = self._get_float(right)
        if self._embedded_double != r:
            return trueObject
        return falseObject

    def prim_less_than(self, right):
        r = self._get_float(right)
        return self._embedded_double < r

    def prim_less_than_or_equal(self, right):
        r = self._get_float(right)
        if self._embedded_double <= r:
            return trueObject
        return falseObject

    def prim_greater_than(self, right):
        r = self._get_float(right)
        if self._embedded_double > r:
            return trueObject
        return falseObject

    def prim_greater_than_or_equal(self, right):
        r = self._get_float(right)
        if self._embedded_double >= r:
            return trueObject
        return falseObject
