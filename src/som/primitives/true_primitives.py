from som.interp_type import is_ast_interpreter
from som.primitives.primitives import Primitives
from som.vm.globals import trueObject, falseObject, nilObject
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive

if is_ast_interpreter():
    from som.vmobjects.block_ast import AstBlock as _Block
else:
    from som.vmobjects.block_bc import BcBlock as _Block


def _not(_rcvr):
    return falseObject


def _or(_rcvr, _arg):
    return trueObject


def _and_and_if_true(_rcvr, arg):
    if isinstance(arg, _Block):
        block_method = arg.get_method()
        return block_method.invoke_1(arg)
    return arg


def _if_false(_rcvr, _arg):
    return nilObject


def _if_true_if_false(_rcvr, true_block, _false_block):
    if isinstance(true_block, _Block):
        block_method = true_block.get_method()
        return block_method.invoke_1(true_block)
    return true_block


class TruePrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(UnaryPrimitive("not", self.universe, _not))
        self._install_instance_primitive(BinaryPrimitive("or:", self.universe, _or))
        self._install_instance_primitive(BinaryPrimitive("||", self.universe, _or))

        self._install_instance_primitive(
            BinaryPrimitive("and:", self.universe, _and_and_if_true)
        )
        self._install_instance_primitive(
            BinaryPrimitive("&&", self.universe, _and_and_if_true)
        )
        self._install_instance_primitive(
            BinaryPrimitive("ifTrue:", self.universe, _and_and_if_true)
        )
        self._install_instance_primitive(
            BinaryPrimitive("ifFalse:", self.universe, _if_false)
        )

        self._install_instance_primitive(
            TernaryPrimitive("ifTrue:ifFalse:", self.universe, _if_true_if_false)
        )
