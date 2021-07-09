from rlib import jit

from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vm.globals import nilObject, falseObject, trueObject

from som.vmobjects.block_ast import AstBlock
from som.vmobjects.method_ast import AstMethod


class AbstractWhileMessageNode(ExpressionNode):

    _immutable_fields_ = ["_predicate_bool", "_rcvr_expr?", "_body_expr?", "universe"]
    _child_nodes_ = ["_rcvr_expr", "_body_expr"]

    def __init__(
        self, rcvr_expr, body_expr, predicate_bool_obj, universe, source_section
    ):
        ExpressionNode.__init__(self, source_section)
        self._predicate_bool = predicate_bool_obj
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._body_expr = self.adopt_child(body_expr)
        self.universe = universe

    def execute(self, frame):
        rcvr_value = self._rcvr_expr.execute(frame)
        body_block = self._body_expr.execute(frame)

        _do_while(self, rcvr_value, body_block)
        return nilObject


# def get_printable_location_while_value(body_method, node):
#     assert isinstance(body_method, AstMethod)
#     return "while_value: %s" % body_method.merge_point_string()
#
# while_value_driver = jit.JitDriver(
#     greens=['body_method', 'node'], reds='auto',
#     get_printable_location = get_printable_location_while_value)
#
#
# class WhileWithValueReceiver(AbstractWhileMessageNode):
#
#     def execute_evaluated(self, frame, rcvr_value, body_block):
#         if rcvr_value is not self._predicate_bool:
#             return nilObject
#         body_method = body_block.get_method()
#
#         while True:
#             while_value_driver.jit_merge_point(body_method = body_method,
#                                                node        = self)
#             body_method.invoke_1(body_block)


def get_printable_location_while(body_method, condition_method, while_type):
    assert isinstance(condition_method, AstMethod)
    assert isinstance(body_method, AstMethod)

    return "%s while %s: %s" % (
        condition_method.merge_point_string(),
        while_type,
        body_method.merge_point_string(),
    )


while_driver = jit.JitDriver(
    greens=["body_method", "condition_method", "node"],
    reds="auto",
    is_recursive=True,
    get_printable_location=get_printable_location_while,
)


def _do_while(node, rcvr_block, body_block):
    condition_method = rcvr_block.get_method()
    body_method = body_block.get_method()

    if rcvr_block.is_same_context(body_block):
        rcvr_block = body_block

    while True:
        while_driver.jit_merge_point(
            body_method=body_method, condition_method=condition_method, node=node
        )

        # STEFAN: looks stupid but might help the jit
        if rcvr_block is body_block:
            rcvr_block = body_block

        condition_value = condition_method.invoke_1(rcvr_block)
        if condition_value is not node._predicate_bool:  # pylint: disable=W
            break
        body_method.invoke_1(body_block)


class WhileMessageNode(AbstractWhileMessageNode):
    def execute_evaluated(self, _frame, rcvr, args):
        _do_while(self, rcvr, args[0])
        return nilObject

    @staticmethod
    def can_specialize(selector, _rcvr, args, _node):
        sel = selector.get_embedded_string()
        return isinstance(args[0], AstBlock) and (
            sel == "whileTrue:" or sel == "whileFalse:"
        )

    @staticmethod
    def specialize_node(selector, _rcvr, _args, node):
        sel = selector.get_embedded_string()
        if sel == "whileTrue:":
            return node.replace(
                WhileMessageNode(
                    node._rcvr_expr,  # pylint: disable=protected-access
                    node._arg_exprs[0],  # pylint: disable=protected-access
                    trueObject,
                    node.universe,
                    node.source_section,
                )
            )
        assert sel == "whileFalse:"
        return node.replace(
            WhileMessageNode(
                node._rcvr_expr,  # pylint: disable=protected-access
                node._arg_exprs[0],  # pylint: disable=protected-access
                falseObject,
                node.universe,
                node.source_section,
            )
        )
