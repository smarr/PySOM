from som.interpreter.ast.nodes.expression_node import ExpressionNode


class IntIncrementNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?"]
    _child_nodes_ = ["_rcvr_expr"]

    def __init__(self, rcvr_expr, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)

    def execute(self, frame):
        result = self._rcvr_expr.execute(frame)
        return result.prim_inc()
