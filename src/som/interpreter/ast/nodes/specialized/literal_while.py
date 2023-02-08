from rlib.jit import JitDriver

from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vm.globals import trueObject, falseObject, nilObject


def get_printable_location_while(self):
    assert isinstance(self, WhileInlinedNode)

    return "while " + str(self.source_section)


while_driver = JitDriver(
    greens=["self"],
    reds=["frame"],
    is_recursive=True,
    get_printable_location=get_printable_location_while,
)


class WhileInlinedNode(ExpressionNode):
    _immutable_fields_ = [
        "_condition_expr?",
        "_body_expr?",
        "_expected_bool",
        "_not_expected_bool",
    ]
    _child_nodes_ = ["_condition_expr", "_body_expr"]

    def __init__(self, condition_expr, body_expr, while_true, source_section):
        ExpressionNode.__init__(self, source_section)
        self._condition_expr = self.adopt_child(condition_expr)
        self._body_expr = self.adopt_child(body_expr)
        self._expected_bool = trueObject if while_true else falseObject
        self._not_expected_bool = falseObject if while_true else trueObject

    def execute(self, frame):
        while True:
            while_driver.jit_merge_point(self=self, frame=frame)

            cond = self._condition_expr.execute(frame)
            if cond is self._expected_bool:
                self._body_expr.execute(frame)
            elif cond is self._not_expected_bool:
                return nilObject
            else:
                raise NotImplementedError(
                    "Would need to generalize, but we haven't implemented that "
                    + "for the bytecode interpreter either"
                )
