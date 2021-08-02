from rlib import jit

from som.primitives.primitives import Primitives
from som.vm.globals import nilObject, trueObject, falseObject
from som.vmobjects.primitive import Primitive, BinaryPrimitive


def _restart(ivkbl, rcvr, args):
    raise RuntimeError(
        "Restart primitive is not supported, #whileTrue: "
        "and #whileTrue: are intrisified so that #restart "
        "is not needed."
    )


def get_printable_location(method_body, method_condition, _while_type):
    from som.vmobjects.method import AbstractMethod

    assert isinstance(method_body, AbstractMethod)
    assert isinstance(method_condition, AbstractMethod)

    return "[%s] while [%s]" % (
        method_condition.merge_point_string(),
        method_body.merge_point_string(),
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


class BlockPrimitivesBase(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("whileTrue:", _while_true))
        self._install_instance_primitive(BinaryPrimitive("whileFalse:", _while_false))
        self._install_instance_primitive(Primitive("restart", _restart))
