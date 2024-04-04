from rlib.objectmodel import compute_hash
from som.primitives.primitives import Primitives

from som.vm.globals import trueObject, falseObject
from som.vm.symbols import symbol_for
from som.vmobjects.integer import Integer
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive
from som.vmobjects.string import String


def _concat(rcvr, argument):
    return String(rcvr.get_embedded_string() + argument.get_embedded_string())


def _as_symbol(rcvr):
    return symbol_for(rcvr.get_embedded_string())


def _length(rcvr):
    return Integer(len(rcvr.get_embedded_string()))


def _equals(op1, op2):
    if (
        isinstance(op2, String)
        and op1.get_embedded_string() == op2.get_embedded_string()
    ):
        return trueObject
    return falseObject


def _substring(rcvr, start, end):
    s = start.get_embedded_integer() - 1
    e = end.get_embedded_integer()
    string = rcvr.get_embedded_string()

    if s < 0 or s >= len(string) or e > len(string) or e < s:
        return String("Error - index out of bounds")
    return String(string[s:e])


def _char_at(rcvr, idx):
    i = idx.get_embedded_integer() - 1
    string = rcvr.get_embedded_string()

    if i < 0 or i >= len(string):
        return String("Error - index out of bounds")
    return String(string[i])


def _hashcode(rcvr):
    return Integer(compute_hash(rcvr.get_embedded_string()))


def _is_whitespace(self):
    string = self.get_embedded_string()

    for char in string:
        if not char.isspace():
            return falseObject

    if len(string) > 0:
        return trueObject
    return falseObject


def _is_letters(self):
    string = self.get_embedded_string()

    for char in string:
        if not char.isalpha():
            return falseObject

    if len(string) > 0:
        return trueObject
    return falseObject


def _is_digits(self):
    string = self.get_embedded_string()

    for char in string:
        if not char.isdigit():
            return falseObject

    if len(string) > 0:
        return trueObject
    return falseObject


class StringPrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("charAt:", _char_at))
        self._install_instance_primitive(BinaryPrimitive("concatenate:", _concat))
        self._install_instance_primitive(UnaryPrimitive("asSymbol", _as_symbol))
        self._install_instance_primitive(UnaryPrimitive("length", _length))
        self._install_instance_primitive(BinaryPrimitive("=", _equals))
        self._install_instance_primitive(
            TernaryPrimitive("primSubstringFrom:to:", _substring)
        )
        self._install_instance_primitive(UnaryPrimitive("hashcode", _hashcode))

        self._install_instance_primitive(UnaryPrimitive("isWhiteSpace", _is_whitespace))
        self._install_instance_primitive(UnaryPrimitive("isLetters", _is_letters))
        self._install_instance_primitive(UnaryPrimitive("isDigits", _is_digits))
