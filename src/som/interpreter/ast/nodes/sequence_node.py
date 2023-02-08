from rlib.jit import unroll_safe

from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.variable_node import LocalFrameVarReadNode


class SequenceNode(ExpressionNode):
    _immutable_fields_ = ["_exprs?[*]"]
    _child_nodes_ = ["_exprs[*]"]

    def __init__(self, expressions, source_section):
        ExpressionNode.__init__(self, source_section)
        self._exprs = self.adopt_children(expressions)

    def execute(self, frame):
        self._execute_all_but_last(frame)
        return self._exprs[-1].execute(frame)

    @unroll_safe
    def _execute_all_but_last(self, frame):
        for i in range(0, len(self._exprs) - 1):
            self._exprs[i].execute(frame)

    def create_trivial_method(self, signature):
        if len(self._exprs) != 2:
            return None

        return_exp = self._exprs[1]
        if isinstance(return_exp, LocalFrameVarReadNode) and return_exp.is_self():
            expr = self._exprs[0]
            if expr.is_trivial_in_sequence():
                return expr.create_trivial_method(signature)

        return None
