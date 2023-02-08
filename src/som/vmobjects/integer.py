from rlib.arithmetic import ovfcheck, bigint_from_int, divrem, IntType
from rlib.llop import as_32_bit_signed_value, int_mod, Signed

from som.vmobjects.abstract_object import AbstractObject
from som.vm.globals import trueObject, falseObject


class Integer(AbstractObject):
    _immutable_fields_ = ["_embedded_integer"]

    def __init__(self, value):
        AbstractObject.__init__(self)
        assert isinstance(value, IntType), "Value: " + str(value)
        self._embedded_integer = value

    def get_embedded_integer(self):
        return self._embedded_integer

    def __str__(self):
        return str(self._embedded_integer)

    def get_class(self, universe):
        return universe.integer_class

    def get_object_layout(self, universe):
        return universe.integer_layout

    def _to_double(self):
        from som.vmobjects.double import Double

        return Double(float(self._embedded_integer))

    def prim_less_than(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        # Check second parameter type:
        if isinstance(right, BigInteger):
            return bigint_from_int(self._embedded_integer).lt(
                right.get_embedded_biginteger()
            )
        if isinstance(right, Double):
            return self._to_double().prim_less_than(right)
        return self._embedded_integer < right.get_embedded_integer()

    def prim_less_than_or_equal(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        # Check second parameter type:
        if isinstance(right, BigInteger):
            result = bigint_from_int(self._embedded_integer).le(
                right.get_embedded_biginteger()
            )
        elif isinstance(right, Double):
            return self._to_double().prim_less_than_or_equal(right)
        else:
            result = self._embedded_integer <= right.get_embedded_integer()

        if result:
            return trueObject
        return falseObject

    def prim_greater_than(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        # Check second parameter type:
        if isinstance(right, BigInteger):
            result = bigint_from_int(self._embedded_integer).gt(
                right.get_embedded_biginteger()
            )
        elif isinstance(right, Double):
            return self._to_double().prim_greater_than(right)
        else:
            result = self._embedded_integer > right.get_embedded_integer()

        if result:
            return trueObject
        return falseObject

    def prim_greater_than_or_equal(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        # Check second parameter type:
        if isinstance(right, BigInteger):
            result = bigint_from_int(self._embedded_integer).ge(
                right.get_embedded_biginteger()
            )
        elif isinstance(right, Double):
            return self._to_double().prim_greater_than_or_equal(right)
        else:
            result = self._embedded_integer >= right.get_embedded_integer()

        if result:
            return trueObject
        return falseObject

    def prim_as_string(self):
        from som.vmobjects.string import String

        return String(str(self._embedded_integer))

    def prim_as_double(self):
        from som.vmobjects.double import Double

        return Double(float(self._embedded_integer))

    def prim_abs(self):
        return Integer(abs(self._embedded_integer))

    def prim_as_32_bit_signed_value(self):
        val = as_32_bit_signed_value(self._embedded_integer)
        return Integer(val)

    def prim_inc(self):
        from som.vmobjects.biginteger import BigInteger

        l = self._embedded_integer
        try:
            result = ovfcheck(l + 1)
            return Integer(result)
        except OverflowError:
            return BigInteger(bigint_from_int(l).add(bigint_from_int(1)))

    def prim_dec(self):
        from som.vmobjects.biginteger import BigInteger

        l = self._embedded_integer
        try:
            result = ovfcheck(l - 1)
            return Integer(result)
        except OverflowError:
            return BigInteger(bigint_from_int(l).sub(bigint_from_int(1)))

    def prim_add(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            return BigInteger(
                right.get_embedded_biginteger().add(
                    bigint_from_int(self._embedded_integer)
                )
            )
        if isinstance(right, Double):
            return self._to_double().prim_add(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        try:
            result = ovfcheck(l + r)
            return Integer(result)
        except OverflowError:
            return BigInteger(bigint_from_int(l).add(bigint_from_int(r)))

    def prim_subtract(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            r = bigint_from_int(self._embedded_integer).sub(
                right.get_embedded_biginteger()
            )
            return BigInteger(r)
        if isinstance(right, Double):
            return self._to_double().prim_subtract(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        try:
            result = ovfcheck(l - r)
            return Integer(result)
        except OverflowError:
            return BigInteger(bigint_from_int(l).sub(bigint_from_int(r)))

    def prim_multiply(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            r = bigint_from_int(self._embedded_integer).mul(
                right.get_embedded_biginteger()
            )
            return BigInteger(r)
        if isinstance(right, Double):
            return self._to_double().prim_multiply(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        try:
            result = ovfcheck(l * r)
            return Integer(result)
        except OverflowError:
            return BigInteger(bigint_from_int(l).mul(bigint_from_int(r)))

    def prim_double_div(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            r = bigint_from_int(self._embedded_integer).truediv(
                right.get_embedded_biginteger()
            )
            return Double(r)
        if isinstance(right, Double):
            return self._to_double().prim_double_div(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        return Double(l / float(r))

    def prim_int_div(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            r = bigint_from_int(self._embedded_integer).floordiv(
                right.get_embedded_biginteger()
            )
            return BigInteger(r)
        if isinstance(right, Double):
            return self._to_double().prim_int_div(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        return Integer(l // r)

    def prim_modulo(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            r = bigint_from_int(self._embedded_integer).mod(
                right.get_embedded_biginteger()
            )
            return BigInteger(r)
        if isinstance(right, Double):
            return self._to_double().prim_modulo(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        return Integer(l % r)

    def prim_remainder(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            _d, r = divrem(
                bigint_from_int(self._embedded_integer), right.get_embedded_biginteger()
            )
            return BigInteger(r)
        if isinstance(right, Double):
            return self._to_double().prim_remainder(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        return Integer(int_mod(Signed, l, r))

    def prim_and(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            r = bigint_from_int(self._embedded_integer).and_(
                right.get_embedded_biginteger()
            )
            return BigInteger(r)
        if isinstance(right, Double):
            return self._to_double().prim_and(right)
        l = self._embedded_integer
        r = right.get_embedded_integer()
        return Integer(l & r)

    def prim_equals(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            result = bigint_from_int(self._embedded_integer).eq(
                right.get_embedded_biginteger()
            )
        elif isinstance(right, Double):
            result = self._embedded_integer == right.get_embedded_double()
        elif isinstance(right, Integer):
            l = self._embedded_integer
            r = right.get_embedded_integer()
            result = l == r
        else:
            return falseObject

        if result:
            return trueObject
        return falseObject

    def prim_unequals(self, right):
        from som.vmobjects.double import Double
        from som.vmobjects.biginteger import BigInteger

        if isinstance(right, BigInteger):
            result = bigint_from_int(self._embedded_integer).ne(
                right.get_embedded_biginteger()
            )
        elif isinstance(right, Double):
            result = self._embedded_integer != right.get_embedded_double()
        elif isinstance(right, Integer):
            l = self._embedded_integer
            r = right.get_embedded_integer()
            result = l != r
        else:
            return trueObject

        if result:
            return trueObject
        return falseObject


int_0 = Integer(0)
int_1 = Integer(1)
