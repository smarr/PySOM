from rlib import jit
from som.interpreter.ast.nodes.specialized.to_do_node import AbstractToDoNode

from som.vmobjects.block_ast import AstBlock
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer
from som.vmobjects.method_ast import AstMethod


def get_printable_location(block_method):
    assert isinstance(block_method, AstMethod)
    return "#to:do: %s" % block_method.merge_point_string()


int_driver = jit.JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    # virtualizables=['frame'],
    get_printable_location=get_printable_location,
)


class IntDownToIntDoNode(AbstractToDoNode):
    @staticmethod
    def _do_loop(rcvr, limit, body_block):
        block_method = body_block.get_method()

        i = rcvr.get_embedded_integer()
        bottom = limit.get_embedded_integer()
        while i >= bottom:
            int_driver.jit_merge_point(block_method=block_method)
            block_method.invoke_2(body_block, Integer(i))
            i -= 1

    @staticmethod
    def can_specialize(selector, rcvr, args, _node):
        return (
            isinstance(args[0], Integer)
            and isinstance(rcvr, Integer)
            and len(args) > 1
            and isinstance(args[1], AstBlock)
            and selector.get_embedded_string() == "downTo:do:"
        )

    @staticmethod
    def specialize_node(_selector, _rcvr, _args, node):
        return node.replace(
            IntDownToIntDoNode(
                node._rcvr_expr,  # pylint: disable=protected-access
                node._arg_exprs[0],  # pylint: disable=protected-access
                node._arg_exprs[1],  # pylint: disable=protected-access
                node.universe,
                node.source_section,
            )
        )


double_driver = jit.JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    # virtualizables=['frame'],
    get_printable_location=get_printable_location,
)


class IntDownToDoubleDoNode(AbstractToDoNode):
    @staticmethod
    def _do_loop(rcvr, limit, body_block):
        block_method = body_block.get_method()

        i = rcvr.get_embedded_integer()
        bottom = limit.get_embedded_double()
        while i >= bottom:
            double_driver.jit_merge_point(block_method=block_method)
            block_method.invoke_2(body_block, Integer(i))
            i -= 1

    @staticmethod
    def can_specialize(selector, rcvr, args, _node):
        return (
            isinstance(args[0], Double)
            and isinstance(rcvr, Integer)
            and len(args) > 1
            and isinstance(args[1], AstBlock)
            and selector.get_embedded_string() == "downTo:do:"
        )

    @staticmethod
    def specialize_node(_selector, _rcvr, _args, node):
        return node.replace(
            IntDownToDoubleDoNode(
                node._rcvr_expr,  # pylint: disable=protected-access
                node._arg_exprs[0],  # pylint: disable=protected-access
                node._arg_exprs[1],  # pylint: disable=protected-access
                node.universe,
                node.source_section,
            )
        )
