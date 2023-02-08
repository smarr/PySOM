from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vm.globals import trueObject, falseObject


class AndInlinedNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?", "_arg_expr?"]
    _child_nodes_ = ["_rcvr_expr", "_arg_expr"]

    def __init__(self, rcvr_expr, arg_expr, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._arg_expr = self.adopt_child(arg_expr)

    def execute(self, frame):
        result = self._rcvr_expr.execute(frame)
        if result is trueObject:
            return self._arg_expr.execute(frame)
        assert result is falseObject
        return falseObject


class OrInlinedNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?", "_arg_expr?"]
    _child_nodes_ = ["_rcvr_expr", "_arg_expr"]

    def __init__(self, rcvr_expr, arg_expr, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._arg_expr = self.adopt_child(arg_expr)

    def execute(self, frame):
        result = self._rcvr_expr.execute(frame)
        if result is trueObject:
            return trueObject
        assert result is falseObject
        return self._arg_expr.execute(frame)
