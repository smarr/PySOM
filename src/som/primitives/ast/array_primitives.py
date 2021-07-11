from rlib import jit
from som.primitives.array_primitives import ArrayPrimitivesBase as _Base
from som.vmobjects.block_ast import AstBlock
from som.vmobjects.method_ast import AstMethod
from som.vmobjects.primitive import BinaryPrimitive


def get_do_index_printable_location(block_method):
    assert isinstance(block_method, AstMethod)
    return "#doIndexes: %s" % block_method.merge_point_string()


do_index_driver = jit.JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    get_printable_location=get_do_index_printable_location,
)


def _do_indexes(rcvr, block):
    from som.vmobjects.integer import Integer

    block_method = block.get_method()

    i = 1
    length = rcvr.get_number_of_indexable_fields()
    while i <= length:  # the i is propagated to Smalltalk, so, start with 1
        do_index_driver.jit_merge_point(block_method=block_method)
        block_method.invoke_2(block, Integer(i))
        i += 1


def get_do_printable_location(block_method):
    assert isinstance(block_method, AstMethod)
    return "#doIndexes: %s" % block_method.merge_point_string()


do_driver = jit.JitDriver(
    greens=["block_method"],
    reds="auto",
    get_printable_location=get_do_printable_location,
)


def _do(rcvr, block):
    block_method = block.get_method()

    i = 0
    length = rcvr.get_number_of_indexable_fields()
    while i < length:  # the array itself is zero indexed
        do_driver.jit_merge_point(block_method=block_method)
        block_method.invoke_2(block, rcvr.get_indexable_field(i))
        i += 1


def _put_all(rcvr, arg):
    if isinstance(arg, AstBlock):
        rcvr.set_all_with_block(arg)
        return rcvr

    # It is a simple value, just put it into the array

    # TODO: move to array, and adapt to use strategies
    rcvr.set_all(arg)
    return rcvr


class ArrayPrimitives(_Base):
    def install_primitives(self):
        _Base.install_primitives(self)
        self._install_instance_primitive(
            BinaryPrimitive("doIndexes:", self.universe, _do_indexes)
        )
        self._install_instance_primitive(BinaryPrimitive("do:", self.universe, _do))
        self._install_instance_primitive(
            BinaryPrimitive("putAll:", self.universe, _put_all)
        )
