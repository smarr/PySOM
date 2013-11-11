from som.primitives.primitives import Primitives
from som.vmobjects.primitive   import Primitive
from som.vmobjects.biginteger  import BigInteger
from som.vmobjects.integer     import Integer
from som.vmobjects.double      import Double
from som.vmobjects.string      import String

import math
import random

class IntegerPrimitives(Primitives):

    
    def _push_long_result(self, frame, result):
        # Check with integer bounds and push:
        if Integer.value_fits(result):
            frame.push(self._universe.new_integer(int(result)))
        else:
            frame.push(self._universe.new_biginteger(result))

    def _resend_as_biginteger(self, operator, left, right):
        left_biginteger = self._universe.new_biginteger(left.get_embedded_integer())
        operands = [right]
        left_biginteger.send(operator, operands, self._universe, self._universe.get_interpreter())

    def _resend_as_double(self, operator, left, right):
        left_double = self._universe.new_double(left.get_embedded_integer())
        operands    = [right]
        left_double.send(operator, operands, self._universe, self._universe.get_interpreter())

    def install_primitives(self):
        def _asString(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(self._universe.new_string(str(rcvr.get_embedded_integer())))
        self._install_instance_primitive(Primitive("asString", self._universe, _asString))

        def _sqrt(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            
            res = math.sqrt(rcvr.get_embedded_integer())
            if res == float(int(res)):
                frame.push(self._universe.new_integer(int(res)))
            else:
                frame.push(self._universe.new_double(res))
        self._install_instance_primitive(Primitive("sqrt", self._universe, _sqrt))

        def _atRandom(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(self._universe.new_integer(int(rcvr.get_embedded_integer() * random.random())))
        self._install_instance_primitive(Primitive("atRandom", self._universe, _atRandom))

        def _plus(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("+", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("+", left, right_obj)
            else:
                # Do operation:
                right = right_obj
                result = left.get_embedded_integer() + right.get_embedded_integer()
                self._push_long_result(frame, result)
        self._install_instance_primitive(Primitive("+", self._universe, _plus))

        def _minus(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("-", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("-", left, right_obj)
            else:
                # Do operation:
                right = right_obj
                result = left.get_embedded_integer() - right.get_embedded_integer()
                self._push_long_result(frame, result)
        self._install_instance_primitive(Primitive("-", self._universe, _minus))


        def _mult(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("*", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("*", left, right_obj)
            else:
                # Do operation:
                right = right_obj
                result = left.get_embedded_integer() * right.get_embedded_integer()
                self._push_long_result(frame, result)
        self._install_instance_primitive(Primitive("*", self._universe, _mult))

        def _doubleDiv(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("/", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("/", left, right_obj)
            else:
                # Do operation:
                right = right_obj
                result = float(left.get_embedded_integer()) / float(right.get_embedded_integer())
                frame.push(self._universe.new_double(result))
        self._install_instance_primitive(Primitive("//", self._universe, _doubleDiv))

        def _intDiv(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("/", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("/", left, right_obj)
            else:
                # Do operation:
                right = right_obj
                result = left.get_embedded_integer() / right.get_embedded_integer()
                self._push_long_result(frame, result)
        self._install_instance_primitive(Primitive("/", self._universe, _intDiv))

        def _mod(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("%", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("%", left, right_obj)
            else:
                # Do operation:
                self._push_long_result(frame, left.get_embedded_integer() % right_obj.get_embedded_integer())
        self._install_instance_primitive(Primitive("%", self._universe, _mod))

        def _and(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()

            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("&", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("&", left, right_obj)
            else:
                # Do operation:
                right = right_obj
                result = left.get_embedded_integer() & right.get_embedded_integer()
                self._push_long_result(frame, result)
        self._install_instance_primitive(Primitive("&", self._universe, _and))

        def _equals(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()
            
            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("=", left, right_obj)
            elif isinstance(right_obj, Integer):
                if left.get_embedded_integer() == right_obj.get_embedded_integer():
                    frame.push(self._universe.trueObject)
                else:
                    frame.push(self._universe.falseObject)
            elif isinstance(right_obj, Double):
                if left.get_embedded_integer() == right_obj.get_embedded_double():
                    frame.push(self._universe.trueObject)
                else:
                    frame.push(self._universe.falseObject)
            else:
                frame.push(self._universe.falseObject)

        self._install_instance_primitive(Primitive("=", self._universe, _equals))

        def _lessThan(ivkbl, frame, interpreter):
            right_obj = frame.pop()
            left      = frame.pop()
            
            # Check second parameter type:
            if isinstance(right_obj, BigInteger):
                # Second operand was BigInteger
                self._resend_as_biginteger("<", left, right_obj)
            elif isinstance(right_obj, Double):
                self._resend_as_double("<", left, right_obj)
            else:
                if left.get_embedded_integer() < right_obj.get_embedded_integer():
                    frame.push(self._universe.trueObject)
                else:
                    frame.push(self._universe.falseObject)
        self._install_instance_primitive(Primitive("<", self._universe, _lessThan))
        
        def _fromString(ivkbl, frame, interpreter):
            param = frame.pop()
            frame.pop()
            
            if not isinstance(param, String):
                frame.push(self._universe.nilObject)
                return
            
            int_value = int(param.get_embedded_string())
            frame.push(self._universe.new_integer(int_value))
        self._install_class_primitive(Primitive("fromString:", self._universe, _fromString))
