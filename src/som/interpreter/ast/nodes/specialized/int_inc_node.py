from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.literal_node import LiteralNode
from som.interpreter.ast.nodes.message.generic_node import BinarySend
from som.vm.symbols import symbol_for
from som.vmobjects.biginteger import BigInteger
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer


class IntIncrementNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?", "_inc_val", "_is_subtract"]
    _child_nodes_ = ["_rcvr_expr"]

    def __init__(self, rcvr_expr, inc_val, is_subtract, universe, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._inc_val = inc_val
        self._is_subtract = is_subtract
        self._universe = universe

    def execute(self, frame):
        result = self._rcvr_expr.execute(frame)
        if (
            isinstance(result, Integer)
            or isinstance(result, Double)
            or isinstance(result, BigInteger)
        ):
            r = result.prim_inc(self._inc_val)
            return r

        return self._make_generic_send(result)

    def does_access_field(self, field_idx):
        from som.interpreter.ast.nodes.field_node import FieldReadNode

        rcvr = self._rcvr_expr
        return isinstance(rcvr, FieldReadNode) and field_idx == rcvr.field_idx

    def create_field_increment_node(self, self_exp, field_idx, source_section):
        from som.interpreter.ast.nodes.supernodes.field_inc_node import (
            FieldIncrementNode,
        )

        return FieldIncrementNode(self_exp, field_idx, self._inc_val, source_section)

    def _make_generic_send(self, receiver):
        int_val = Integer(-self._inc_val if self._is_subtract else self._inc_val)
        literal = LiteralNode(int_val, self.source_section)
        node = BinarySend(
            symbol_for("-" if self._is_subtract else "+"),
            self._universe,
            self._rcvr_expr,
            literal,
            self.source_section,
        )

        self.replace(node)
        return node.exec_evaluated_2(receiver, int_val)
