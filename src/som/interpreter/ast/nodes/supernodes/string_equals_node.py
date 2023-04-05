from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.literal_node import LiteralNode
from som.interpreter.ast.nodes.message.generic_node import BinarySend
from som.vm.globals import falseObject, trueObject
from som.vm.symbols import symbol_for
from som.vmobjects.string import String


class StringEqualsNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?", "_str", "_universe"]
    _child_nodes_ = ["_rcvr_expr"]

    def __init__(self, rcvr_expr, str_obj, universe, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._universe = universe
        self._str = str_obj.get_embedded_string()

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        if isinstance(rcvr, String):
            if rcvr.get_embedded_string() == self._str:
                return trueObject
            return falseObject

        return self._make_generic_send(rcvr)

    def _make_generic_send(self, receiver):
        str_obj = String(self._str)
        node = BinarySend(
            symbol_for("="),
            self._universe,
            self._rcvr_expr,
            LiteralNode(str_obj, self.source_section),
            self.source_section,
        )
        self.replace(node)
        return node.exec_evaluated_2(receiver, str_obj)
