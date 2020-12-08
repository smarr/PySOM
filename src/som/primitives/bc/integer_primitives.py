from rlib import jit

from som.primitives.integer_primitives import IntegerPrimitivesBase as _Base
from som.vmobjects.double import Double
from som.vmobjects.integer     import Integer
from som.vmobjects.primitive   import Primitive

from som.vmobjects.block_bc import block_evaluate, BcBlock


def get_printable_location(interpreter, block_method):
    from som.vmobjects.method_bc import BcMethod
    assert isinstance(block_method, BcMethod)
    return "to:do: [%s>>%s]" % (block_method.get_holder().get_name().get_embedded_string(),
                                block_method.get_signature().get_embedded_string())


jitdriver_int = jit.JitDriver(
    name='to:do: with int',
    greens=['interpreter', 'block_method'],
    reds='auto',
    # virtualizables=['frame'],
    is_recursive=True,
    get_printable_location=get_printable_location)

jitdriver_double = jit.JitDriver(
    name='to:do: with double',
    greens=['interpreter', 'block_method'],
    reds='auto',
    # virtualizables=['frame'],
    is_recursive=True,
    get_printable_location=get_printable_location)


def _to_do_int(i, by_increment, top, frame, context, interpreter, block_method):
    assert isinstance(i, int)
    assert isinstance(top, int)
    while i <= top:
        jitdriver_int.jit_merge_point(interpreter=interpreter,
                                      block_method=block_method)

        b = BcBlock(block_method, context)
        frame.push(b)
        frame.push(Integer(i))
        block_evaluate(b, interpreter, frame)
        frame.pop()
        i += by_increment


def _to_do_double(i, by_increment, top, frame, context, interpreter, block_method):
    assert isinstance(i, int)
    assert isinstance(top, float)
    while i <= top:
        jitdriver_double.jit_merge_point(interpreter=interpreter,
                                         block_method=block_method)

        b = BcBlock(block_method, context)
        frame.push(b)
        frame.push(Integer(i))
        block_evaluate(b, interpreter, frame)
        frame.pop()
        i += by_increment


def _to_do(ivkbl, frame, interpreter):
    block = frame.pop()
    limit = frame.pop()
    self  = frame.pop()  # we do leave it on there

    block_method = block.get_method()
    context      = block.get_context()

    i = self.get_embedded_integer()
    if isinstance(limit, Double):
        _to_do_double(i, 1, limit.get_embedded_double(), frame, context, interpreter,
                      block_method)
    else:
        _to_do_int(i, 1, limit.get_embedded_integer(), frame, context, interpreter,
                   block_method)

    frame.push(self)


def _to_by_do(ivkbl, frame, interpreter):
    block = frame.pop()
    by_increment = frame.pop()
    limit = frame.pop()
    self  = frame.pop()  # we do leave it on there

    block_method = block.get_method()
    context      = block.get_context()

    i = self.get_embedded_integer()
    if isinstance(limit, Double):
        _to_do_double(i, by_increment.get_embedded_integer(), limit.get_embedded_double(), frame, context, interpreter,
                      block_method)
    else:
        _to_do_int(i, by_increment.get_embedded_integer(), limit.get_embedded_integer(), frame, context, interpreter,
                   block_method)

    frame.push(self)


class IntegerPrimitives(_Base):

    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(Primitive("to:do:", self._universe, _to_do))
        self._install_instance_primitive(Primitive("to:by:do:", self._universe, _to_by_do))
