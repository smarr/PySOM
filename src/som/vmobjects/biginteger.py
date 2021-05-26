from rlib.arithmetic import bigint_from_int, divrem, bigint_type
from .abstract_object import AbstractObject
from som.vm.globals import trueObject, falseObject


class BigInteger(AbstractObject):

    _immutable_fields_ = ["_embedded_biginteger"]

    def __init__(self, value):
        AbstractObject.__init__(self)
        assert isinstance(value, bigint_type)
        self._embedded_biginteger = value

    def get_embedded_biginteger(self):
        return self._embedded_biginteger

    def __str__(self):
        return str(self._embedded_biginteger)

    def get_class(self, universe):
        return universe.integerClass

    def quick_add(self, from_method, frame, interpreter, bytecode_index):
        right = frame.pop()
        frame.pop()
        frame.push(self.prim_add(right))

    def quick_multiply(self, from_method, frame, interpreter, bytecode_index):
        right = frame.pop()
        frame.pop()
        frame.push(self.prim_multiply(right))

    def quick_subtract(self, from_method, frame, interpreter, bytecode_index):
        right = frame.pop()
        frame.pop()
        frame.push(self.prim_subtract(right))

    def _to_double(self):
        from .double import Double
        return Double(self._embedded_biginteger.tofloat())

    def prim_less_than(self, right):
        from .double import Double
        # Check second parameter type:
        if isinstance(right, Double):
            return self._to_double().prim_less_than(right)
        if not isinstance(right, BigInteger):
            result = self._embedded_biginteger.lt(
                bigint_from_int(right.get_embedded_integer()))
        else:
            result = self._embedded_biginteger.lt(
                right.get_embedded_biginteger())

        if result:
            return trueObject
        else:
            return falseObject

    def prim_less_than_or_equal(self, right):
        from .double import Double
        # Check second parameter type:
        if isinstance(right, Double):
            return self._to_double().prim_less_than_or_equal(right)
        if not isinstance(right, BigInteger):
            result = self._embedded_biginteger.le(
                bigint_from_int(right.get_embedded_integer()))
        else:
            result = self._embedded_biginteger.le(
                right.get_embedded_biginteger())

        if result:
            return trueObject
        else:
            return falseObject

    def prim_greater_than(self, right):
        from .double import Double
        # Check second parameter type:
        if isinstance(right, Double):
            return self._to_double().prim_greater_than(right)
        if not isinstance(right, BigInteger):
            result = self._embedded_biginteger.gt(
                bigint_from_int(right.get_embedded_integer()))
        else:
            result = self._embedded_biginteger.gt(
                right.get_embedded_biginteger())

        if result:
            return trueObject
        else:
            return falseObject

    def prim_as_string(self):
        from .string import String
        return String(self._embedded_biginteger.str())

    def prim_as_double(self):
        from .double import Double
        return Double(self._embedded_biginteger.tofloat())

    def prim_abs(self):
        return BigInteger(self._embedded_biginteger.abs())

    def prim_as_32_bit_signed_value(self):
        from .integer import Integer
        return Integer(self._embedded_biginteger.digit(0))

    def prim_max(self, right):
        if isinstance(right, BigInteger):
            if right.get_embedded_biginteger().gt(self._embedded_biginteger):
                return right
            return self
        from .integer import Integer
        assert isinstance(right, Integer)

        right_big = bigint_from_int(right.get_embedded_integer())
        if right_big.gt(self._embedded_biginteger):
            return right
        return self

    def prim_add(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            return BigInteger(
                right.get_embedded_biginteger().add(self._embedded_biginteger))
        elif isinstance(right, Double):
            return self._to_double().prim_add(right)
        else:
            return BigInteger(
                bigint_from_int(right.get_embedded_integer()).add(
                    self._embedded_biginteger))

    def prim_subtract(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            r = self._embedded_biginteger.sub(right.get_embedded_biginteger())
        elif isinstance(right, Double):
            return self._to_double().prim_subtract(right)
        else:
            r = self._embedded_biginteger.sub(bigint_from_int(
                right.get_embedded_integer()))
        return BigInteger(r)

    def prim_multiply(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            r = self._embedded_biginteger.mul(right.get_embedded_biginteger())
        elif isinstance(right, Double):
            return self._to_double().prim_multiply(right)
        else:
            r = self._embedded_biginteger.mul(bigint_from_int(
                right.get_embedded_integer()))
        return BigInteger(r)

    def prim_double_div(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            r = self._embedded_biginteger.truediv(
                right.get_embedded_biginteger())
        elif isinstance(right, Double):
            return self._to_double().prim_double_div(right)
        else:
            r = self._embedded_biginteger.truediv(bigint_from_int(
                right.get_embedded_integer()))
        return Double(r)

    def prim_int_div(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            r = self._embedded_biginteger.floordiv(
                right.get_embedded_biginteger())
        elif isinstance(right, Double):
            return self._to_double().prim_int_div(right)
        else:
            r = self._embedded_biginteger.floordiv(bigint_from_int(
                right.get_embedded_integer()))
        return BigInteger(r)

    def prim_modulo(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            r = self._embedded_biginteger.mod(
                right.get_embedded_biginteger())
        elif isinstance(right, Double):
            return self._to_double().prim_modulo(right)
        else:
            r = self._embedded_biginteger.mod(bigint_from_int(
                right.get_embedded_integer()))
        return BigInteger(r)

    def prim_remainder(self, right):
        from .integer import Integer

        if isinstance(right, BigInteger):
            right_val = self._embedded_biginteger
        else:
            assert isinstance(right, Integer)
            right_val = bigint_from_int(right.get_embedded_integer())

        _d, r = divrem(self._embedded_biginteger,
                        right_val)
        return BigInteger(r)

    def prim_and(self, right):
        from .double import Double
        if isinstance(right, BigInteger):
            r = self._embedded_biginteger.and_(
                right.get_embedded_biginteger())
        elif isinstance(right, Double):
            return self._to_double().prim_modulo(right)
        else:
            r = self._embedded_biginteger.and_(bigint_from_int(
                right.get_embedded_integer()))
        return BigInteger(r)

    def prim_equals(self, right):
        from .double import Double
        from .integer import Integer
        if isinstance(right, BigInteger):
            result = self._embedded_biginteger.eq(
                right.get_embedded_biginteger())
        elif isinstance(right, Double):
            result = (self._embedded_biginteger.tofloat()
                      == right.get_embedded_double())
        elif isinstance(right, Integer):
            r = right.get_embedded_integer()
            result = self._embedded_biginteger.eq(bigint_from_int(r))
        else:
            return falseObject

        if result:
            return trueObject
        else:
            return falseObject

    def prim_unequals(self, right):
        from .double import Double
        from .integer import Integer
        if isinstance(right, BigInteger):
            result = self._embedded_biginteger.ne(
                right.get_embedded_biginteger())
        elif isinstance(right, Double):
            result = (self._embedded_biginteger.tofloat()
                      != right.get_embedded_double())
        elif isinstance(right, Integer):
            r = right.get_embedded_integer()
            result = self._embedded_biginteger.ne(bigint_from_int(r))
        else:
            return trueObject

        if result:
            return trueObject
        else:
            return falseObject
