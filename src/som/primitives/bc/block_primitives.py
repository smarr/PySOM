from som.primitives.primitives import Primitives
from som.vmobjects.primitive import BinaryPrimitive
from som.vm.globals import nilObject, trueObject, falseObject

from rlib import jit


def get_printable_location(method_body, method_condition, _while_type):
    from som.vmobjects.method_bc import BcAbstractMethod

    assert isinstance(method_body, BcAbstractMethod)
    assert isinstance(method_condition, BcAbstractMethod)

    return "[%s>>%s] while [%s>>%s]" % (
        method_condition.get_holder().get_name().get_embedded_string(),
        method_condition.get_signature().get_embedded_string(),
        method_body.get_holder().get_name().get_embedded_string(),
        method_body.get_signature().get_embedded_string(),
    )


jitdriver = jit.JitDriver(
    greens=["method_body", "method_condition", "while_type"],
    reds="auto",
    # virtualizables=['frame'],
    is_recursive=True,
    get_printable_location=get_printable_location,
)


def _while_loop(loop_condition, loop_body, while_type):
    method_body = loop_body.get_method()
    method_condition = loop_condition.get_method()

    while True:
        jitdriver.jit_merge_point(
            method_body=method_body,
            method_condition=method_condition,
            while_type=while_type,
        )
        condition_result = method_condition.invoke_1(loop_condition)
        if condition_result is while_type:
            method_body.invoke_1(loop_body)
        else:
            break
    return nilObject


def _while_false(rcvr, arg):
    return _while_loop(rcvr, arg, falseObject)


def _while_true(rcvr, arg):
    return _while_loop(rcvr, arg, trueObject)


class BlockPrimitives(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("whileTrue:", _while_true))
        self._install_instance_primitive(BinaryPrimitive("whileFalse:", _while_false))
