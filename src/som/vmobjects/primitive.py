from som.interp_type import is_ast_interpreter
from som.vmobjects.abstract_object import AbstractObject


class _AbstractPrimitive(AbstractObject):
    _immutable_fields_ = ["_is_empty", "_signature", "_holder"]

    def __init__(self, signature_string, universe, is_empty=False):
        AbstractObject.__init__(self)

        self._signature = universe.symbol_for(signature_string)
        self._is_empty = is_empty
        self._holder = None

    @staticmethod
    def is_primitive():
        return True

    @staticmethod
    def is_invokable():
        """We use this method to identify methods and primitives"""
        return True

    def get_signature(self):
        return self._signature

    def get_holder(self):
        return self._holder

    def set_holder(self, value):
        self._holder = value

    def is_empty(self):
        # By default a primitive is not empty
        return self._is_empty

    def get_class(self, universe):
        return universe.primitive_class

    def __str__(self):
        if self._holder:
            holder = self.get_holder().get_name().get_embedded_string()
        else:
            holder = "nil"
        return "Primitive(" + holder + ">>" + str(self.get_signature()) + ")"


class _AstPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, rcvr, args):
        prim_fn = self._prim_fn
        return prim_fn(self, rcvr, args)


class _AstUnaryPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, rcvr, _args):
        prim_fn = self._prim_fn
        return prim_fn(rcvr)


class _AstBinaryPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, rcvr, args):
        prim_fn = self._prim_fn
        return prim_fn(rcvr, args[0])


class _AstTernaryPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, rcvr, args):
        prim_fn = self._prim_fn
        return prim_fn(rcvr, args[0], args[1])


class _BcPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, frame):
        prim_fn = self._prim_fn
        prim_fn(self, frame)

    def get_number_of_signature_arguments(self):
        return self._signature.get_number_of_signature_arguments()


class _BcUnaryPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, frame):
        prim_fn = self._prim_fn
        rcvr = frame.top()
        result = prim_fn(rcvr)
        frame.set_top(result)

    def get_number_of_signature_arguments(self):
        return 1


class _BcBinaryPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, frame):
        prim_fn = self._prim_fn
        arg = frame.pop()
        rcvr = frame.top()
        result = prim_fn(rcvr, arg)
        frame.set_top(result)

    def get_number_of_signature_arguments(self):
        return 2


class _BcTernaryPrimitive(_AbstractPrimitive):
    _immutable_fields_ = ["_prim_fn"]

    def __init__(self, signature_string, universe, prim_fn, is_empty=False):
        _AbstractPrimitive.__init__(self, signature_string, universe, is_empty)
        self._prim_fn = prim_fn

    def invoke(self, frame):
        prim_fn = self._prim_fn
        arg2 = frame.pop()
        arg1 = frame.pop()
        rcvr = frame.top()
        result = prim_fn(rcvr, arg1, arg2)
        frame.set_top(result)

    def get_number_of_signature_arguments(self):
        return 3


def _empty_invoke(ivkbl, _a=None, _b=None):
    """Write a warning to the screen"""
    print(
        "Warning: undefined primitive #%s called"
        % ivkbl.get_signature().get_embedded_string()
    )


if is_ast_interpreter():
    Primitive = _AstPrimitive
    UnaryPrimitive = _AstUnaryPrimitive
    BinaryPrimitive = _AstBinaryPrimitive
    TernaryPrimitive = _AstTernaryPrimitive
else:
    Primitive = _BcPrimitive
    UnaryPrimitive = _BcUnaryPrimitive
    BinaryPrimitive = _BcBinaryPrimitive
    TernaryPrimitive = _BcTernaryPrimitive


def empty_primitive(signature_string, universe):
    """Return an empty primitive with the given signature"""
    return Primitive(signature_string, universe, _empty_invoke, True)
