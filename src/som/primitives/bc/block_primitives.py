from som.interpreter.ast.frame import get_inner_as_context
from som.interpreter.bc.frame import stack_push, stack_pop
from som.primitives.primitives import Primitives
from som.vmobjects.primitive import Primitive
from som.vmobjects.block_bc import BcBlock
from som.vm.globals import nilObject, trueObject, falseObject

from rlib import jit


def get_printable_location(method_body, method_condition, _while_type):
    from som.vmobjects.method_bc import BcMethod

    assert isinstance(method_body, BcMethod)
    assert isinstance(method_condition, BcMethod)

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


def _execute_block(frame, block_method):
    b = BcBlock(block_method, get_inner_as_context(frame))
    stack_push(frame, b)

    block_method.invoke(frame)
    return stack_pop(frame)


def _while_loop(frame, while_type):
    loop_body = stack_pop(frame)
    loop_condition = stack_pop(frame)

    method_body = loop_body.get_method()
    method_condition = loop_condition.get_method()

    while True:
        jitdriver.jit_merge_point(
            method_body=method_body,
            method_condition=method_condition,
            while_type=while_type,
        )
        condition_result = _execute_block(frame, method_condition)
        if condition_result is while_type:
            _execute_block(frame, method_body)
        else:
            break

    stack_push(frame, nilObject)


def _while_false(_ivkbl, frame):
    _while_loop(frame, falseObject)


def _while_true(_ivkbl, frame):
    _while_loop(frame, trueObject)


class BlockPrimitives(Primitives):
    def install_primitives(self):
        self._install_instance_primitive(
            Primitive("whileTrue:", self.universe, _while_true)
        )
        self._install_instance_primitive(
            Primitive("whileFalse:", self.universe, _while_false)
        )
