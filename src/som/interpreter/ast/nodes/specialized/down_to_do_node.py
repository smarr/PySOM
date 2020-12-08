from rlib import jit
from .to_do_node import AbstractToDoNode

from .....vmobjects.block_ast import AstBlock
from .....vmobjects.double import Double
from .....vmobjects.integer import Integer
from .....vmobjects.method_ast import AstMethod


def get_printable_location(block_method):
    assert isinstance(block_method, AstMethod)
    return "#to:do: %s" % block_method.merge_point_string()


int_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    is_recursive=True,
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntDownToIntDoNode(AbstractToDoNode):

    def _do_loop(self, rcvr, limit, body_block):
        block_method = body_block.get_method()

        i      = rcvr.get_embedded_integer()
        bottom = limit.get_embedded_integer()
        while i >= bottom:
            int_driver.jit_merge_point(block_method = block_method)
            block_method.invoke(body_block, [Integer(i)])
            i -= 1

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Integer) and isinstance(rcvr, Integer) and
                len(args) > 1 and isinstance(args[1], AstBlock) and
                selector.get_embedded_string() == "downTo:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntDownToIntDoNode(node._rcvr_expr, node._arg_exprs[0],
                               node._arg_exprs[1], node._universe,
                               node._source_section))


double_driver = jit.JitDriver(
    greens=['block_method'],
    reds='auto',
    is_recursive=True,
    # virtualizables=['frame'],
    get_printable_location=get_printable_location)


class IntDownToDoubleDoNode(AbstractToDoNode):

    def _do_loop(self, rcvr, limit, body_block):
        block_method = body_block.get_method()

        i      = rcvr.get_embedded_integer()
        bottom = limit.get_embedded_double()
        while i >= bottom:
            double_driver.jit_merge_point(block_method = block_method)
            block_method.invoke(body_block, [Integer(i)])
            i -= 1

    @staticmethod
    def can_specialize(selector, rcvr, args, node):
        return (isinstance(args[0], Double) and isinstance(rcvr, Integer) and
                len(args) > 1 and isinstance(args[1], AstBlock) and
                selector.get_embedded_string() == "downTo:do:")

    @staticmethod
    def specialize_node(selector, rcvr, args, node):
        return node.replace(
            IntDownToDoubleDoNode(node._rcvr_expr, node._arg_exprs[0],
                                  node._arg_exprs[1], node._universe,
                                  node._source_section))
