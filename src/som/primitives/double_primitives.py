from som.primitives.primitives import Primitives
from som.vmobjects.primitive   import Primitive
from som.vmobjects.double      import Double
from som.vmobjects.integer     import Integer

import math

class DoublePrimitives(Primitives):

    def _coerce_to_double(self, obj):
        if isinstance(obj, Double):
            return obj
        if isinstance(obj, Integer):
            return self._universe.new_double(obj.get_embedded_integer())
        raise ValueError("Cannot coerce %s to Double!" % obj)

    def install_primitives(self):        
        def _asString(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(self._universe.new_string(str(rcvr.get_embedded_double())))
        self._install_instance_primitive(Primitive("asString", self._universe, _asString))

        def _sqrt(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(self._universe.new_double(math.sqrt(rcvr.get_embedded_double())))
        self._install_instance_primitive(Primitive("sqrt", self._universe, _sqrt))

        def _plus(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            frame.push(self._universe.new_double(op1.get_embedded_double()
                                                 + op2.get_embedded_double()))
        self._install_instance_primitive(Primitive("+", self._universe, _plus))

        def _minus(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            frame.push(self._universe.new_double(op2.get_embedded_double()
                                                 - op1.get_embedded_double()))
        self._install_instance_primitive(Primitive("-", self._universe, _minus))

        def _mult(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            frame.push(self._universe.new_double(op2.get_embedded_double()
                                                 * op1.get_embedded_double()))
        self._install_instance_primitive(Primitive("*", self._universe, _mult))

        def _doubleDiv(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            frame.push(self._universe.new_double(op2.get_embedded_double()
                                                   / op1.get_embedded_double()))
        self._install_instance_primitive(Primitive("//", self._universe, _doubleDiv))

        def _mod(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            frame.push(self._universe.new_double(op2.get_embedded_double()
                                                 % op1.get_embedded_double()))
        self._install_instance_primitive(Primitive("%", self._universe, _mod))
        
        def _and(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            
            left  = int(op2.get_embedded_double())
            right = int(op1.get_embedded_double())
            result = float(left & right)
            frame.push(interpreter.get_universe().new_double(result))
        self._install_instance_primitive(Primitive("&", self._universe, _and))

        def _bitXor(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            
            left  = int(op2.get_embedded_double())
            right = int(op1.get_embedded_double())
            result = float(left ^ right)
            frame.push(interpreter.get_universe().new_double(result))
        self._install_instance_primitive(Primitive("bitXor:", self._universe, _bitXor))

        def _equals(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            if op1.get_embedded_double() == op2.get_embedded_double():
                frame.push(self._universe.trueObject)
            else:
                frame.push(self._universe.falseObject)
        self._install_instance_primitive(Primitive("=", self._universe, _equals))

        def _lessThan(ivkbl, frame, interpreter):
            op1 = self._coerce_to_double(frame.pop())
            op2 = frame.pop()
            if op2.get_embedded_double() < op1.get_embedded_double():
                frame.push(self._universe.trueObject)
            else:
                frame.push(self._universe.falseObject)
        self._install_instance_primitive(Primitive("<", self._universe, _lessThan))
        
        def _round(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(self._universe.new_integer(int(round(rcvr.get_embedded_double()))))
        self._install_instance_primitive(Primitive("round", self._universe, _round))
