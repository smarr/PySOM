from som.primitives.invokable_primitives import InvokablePrimitivesBase as _Base
from som.vm.globals import nilObject
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.array_strategy  import Array
from som.vmobjects.method_ast      import AstMethod
from som.vmobjects.primitive       import Primitive


def _invoke_on_with(ivkbl, rcvr, args):
    assert isinstance(rcvr,    AstMethod)
    assert isinstance(args[0], AbstractObject)
    assert isinstance(args[1], Array) or args[1] is nilObject

    if args[1] is nilObject:
        direct_args = []
    else:
        direct_args = args[1].as_argument_array()
    return rcvr.invoke(args[0], direct_args)


class MethodPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(Primitive("invokeOn:with:",
                                                   self._universe, _invoke_on_with))
