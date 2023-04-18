from som.interpreter.ast.nodes.message.abstract_node import AbstractMessageNode
from som.interpreter.ast.nodes.message.generic_node import (
    UnarySend,
    BinarySend,
    TernarySend,
    NArySend,
)

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
from som.interpreter.ast.nodes.supernodes.arg_send_node import (
    BinaryArgSend,
    UnaryArgSend,
    TernaryArgSend,
)
from som.interpreter.ast.nodes.variable_node import LocalFrameVarReadNode


class UninitializedMessageNode(AbstractMessageNode):
    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self._specialize(frame, rcvr, args).execute_evaluated(frame, rcvr, args)

    def _specialize(self, _frame, rcvr, args):
        if args:
            for specialization in [
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
        num_args = len(args) + 1

        # need to check the exact type, because we have unsupported subclass supernodes
        is_arg_send = (
            type(self._rcvr_expr)  # pylint: disable=unidiomatic-typecheck
            is LocalFrameVarReadNode
        )

        if num_args == 1:
            if is_arg_send:
                node = UnaryArgSend(
                    self._selector,
                    self.universe,
                    self._rcvr_expr.get_frame_idx(),
                    self.source_section,
                )
            else:
                node = UnarySend(
                    self._selector, self.universe, self._rcvr_expr, self.source_section
                )
        elif num_args == 2:
            if is_arg_send:
                node = BinaryArgSend(
                    self._selector,
                    self.universe,
                    self._rcvr_expr.get_frame_idx(),
                    self._arg_exprs[0],
                    self.source_section,
                )
            else:
                node = BinarySend(
                    self._selector,
                    self.universe,
                    self._rcvr_expr,
                    self._arg_exprs[0],
                    self.source_section,
                )
        elif num_args == 3:
            if is_arg_send:
                node = TernaryArgSend(
                    self._selector,
                    self.universe,
                    self._rcvr_expr.get_frame_idx(),
                    self._arg_exprs[0],
                    self._arg_exprs[1],
                    self.source_section,
                )
            else:
                node = TernarySend(
                    self._selector,
                    self.universe,
                    self._rcvr_expr,
                    self._arg_exprs[0],
                    self._arg_exprs[1],
                    self.source_section,
                )
        else:
            node = NArySend(
                self._selector,
                self.universe,
                self._rcvr_expr,
                self._arg_exprs,
                self.source_section,
            )
        return self.replace(node)
