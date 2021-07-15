from som.interp_type import is_ast_interpreter
from som.primitives.primitives import Primitives
from som.vm.globals import trueObject, falseObject
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive

if is_ast_interpreter():
    from som.vmobjects.block_ast import AstBlock as _Block
else:
    from som.vmobjects.block_bc import BcBlock as _Block


def _not(_rcvr):
    return falseObject


def _or(_rcvr, _arg):
    return trueObject


def _and(_rcvr, arg):
    if isinstance(arg, _Block):
        block_method = arg.get_method()
        return block_method.invoke_1(arg)
    return arg


class TruePrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("not", self.universe, _not))
        self._install_instance_primitive(BinaryPrimitive("or:", self.universe, _or))
        self._install_instance_primitive(BinaryPrimitive("||", self.universe, _or))

        self._install_instance_primitive(BinaryPrimitive("and:", self.universe, _and))
        self._install_instance_primitive(BinaryPrimitive("&&", self.universe, _and))
