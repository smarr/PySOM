from som.interpreter.ast.nodes.message.abstract_node import AbstractMessageNode
from som.interpreter.ast.nodes.message.generic_node import GenericMessageNode

from som.interpreter.ast.nodes.specialized.down_to_do_node import (
    IntDownToIntDoNode,
    IntDownToDoubleDoNode,
)
from som.interpreter.ast.nodes.specialized.if_true_false import (
    IfTrueIfFalseNode,
    IfNode,
)
from som.interpreter.ast.nodes.specialized.to_by_do_node import (
    IntToIntByDoNode,
    IntToDoubleByDoNode,
)
from som.interpreter.ast.nodes.specialized.to_do_node import (
    IntToIntDoNode,
    IntToDoubleDoNode,
)
from som.interpreter.ast.nodes.specialized.while_node import WhileMessageNode


class UninitializedMessageNode(AbstractMessageNode):
    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self._specialize(frame, rcvr, args).execute_evaluated(frame, rcvr, args)

    def _specialize(self, _frame, rcvr, args):
        if args:
            for specialization in [
                WhileMessageNode,
                IntToIntDoNode,
                IntToDoubleDoNode,
                IntToIntByDoNode,
                IntToDoubleByDoNode,
                IntDownToIntDoNode,
                IntDownToDoubleDoNode,
                IfTrueIfFalseNode,
                IfNode,
            ]:
                if specialization.can_specialize(self._selector, rcvr, args, self):
                    return specialization.specialize_node(
                        self._selector, rcvr, args, self
                    )
        return self.replace(
            GenericMessageNode(
                self._selector,
                self.universe,
                self._rcvr_expr,
                self._arg_exprs,
                self.source_section,
            )
        )
