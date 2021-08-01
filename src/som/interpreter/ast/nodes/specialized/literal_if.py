from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vm.globals import trueObject, falseObject, nilObject


class IfInlinedNode(ExpressionNode):
    _immutable_fields_ = [
        "_condition_expr?",
        "_body_expr?",
        "universe",
        "_expected_bool",
        "_not_expected_bool",
    ]
    _child_nodes_ = ["_condition_expr", "_body_expr"]

    def __init__(self, condition_expr, body_expr, if_true, source_section):
        ExpressionNode.__init__(self, source_section)
        self._condition_expr = self.adopt_child(condition_expr)
        self._body_expr = self.adopt_child(body_expr)
        self._expected_bool = trueObject if if_true else falseObject
        self._not_expected_bool = falseObject if if_true else trueObject

    def execute(self, frame):
        result = self._condition_expr.execute(frame)
        if self._expected_bool is result:
            return self._body_expr.execute(frame)
        if result is self._not_expected_bool:
            return nilObject
        raise NotImplementedError(
            "Would need to generalize, but we haven't implemented that "
            + "for the bytecode interpreter either"
        )


class IfElseInlinedNode(ExpressionNode):
    _immutable_fields_ = [
        "_condition_expr?",
        "_true_expr?",
        "_false_expr?",
        "universe",
        "_expected_bool",
        "_not_expected_bool",
    ]
    _child_nodes_ = ["_condition_expr", "_true_expr", "_false_expr"]

    def __init__(self, condition_expr, true_expr, false_expr, if_true, source_section):
        ExpressionNode.__init__(self, source_section)
        self._condition_expr = self.adopt_child(condition_expr)
        self._true_expr = self.adopt_child(true_expr)
        self._false_expr = self.adopt_child(false_expr)

        self._expected_bool = trueObject if if_true else falseObject
        self._not_expected_bool = falseObject if if_true else trueObject

    def execute(self, frame):
        result = self._condition_expr.execute(frame)
        if self._expected_bool is result:
            return self._true_expr.execute(frame)
        if result is self._not_expected_bool:
            return self._false_expr.execute(frame)
        raise NotImplementedError(
            "Would need to generalize, but we haven't implemented that "
            + "for the bytecode interpreter either"
        )
