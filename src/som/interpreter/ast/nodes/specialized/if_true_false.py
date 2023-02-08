from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vm.globals import nilObject, trueObject, falseObject
from som.vmobjects.block_ast import AstBlock


class IfTrueIfFalseNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?", "_true_expr?", "_false_expr?", "universe"]
    _child_nodes_ = ["_rcvr_expr", "_true_expr", "_false_expr"]

    def __init__(self, rcvr_expr, true_expr, false_expr, universe, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._true_expr = self.adopt_child(true_expr)
        self._false_expr = self.adopt_child(false_expr)
        self.universe = universe

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        true = self._true_expr.execute(frame)
        false = self._false_expr.execute(frame)

        return self._do_iftrue_iffalse(rcvr, true, false)

    def execute_evaluated(self, _frame, rcvr, args):
        return self._do_iftrue_iffalse(rcvr, args[0], args[1])

    @staticmethod
    def _do_iftrue_iffalse(rcvr, true, false):
        if rcvr is trueObject:
            if isinstance(true, AstBlock):
                return true.get_method().invoke_1(true)
            return true

        assert rcvr is falseObject
        if isinstance(false, AstBlock):
            return false.get_method().invoke_1(false)
        return false

    @staticmethod
    def can_specialize(selector, rcvr, args, _node):
        return (
            len(args) == 2
            and (rcvr is trueObject or rcvr is falseObject)
            and selector.get_embedded_string() == "ifTrue:ifFalse:"
        )

    @staticmethod
    def specialize_node(_selector, _rcvr, _args, node):
        return node.replace(
            IfTrueIfFalseNode(
                node._rcvr_expr,  # pylint: disable=protected-access
                node._arg_exprs[0],  # pylint: disable=protected-access
                node._arg_exprs[1],  # pylint: disable=protected-access
                node.universe,
                node.source_section,
            )
        )


class IfNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr_expr?", "_branch_expr?", "_condition", "universe"]
    _child_nodes_ = ["_rcvr_expr", "_branch_expr"]

    def __init__(self, rcvr_expr, branch_expr, condition_obj, universe, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._branch_expr = self.adopt_child(branch_expr)
        self._condition = condition_obj
        self.universe = universe

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        branch = self._branch_expr.execute(frame)
        return self._do_if(rcvr, branch)

    def execute_evaluated(self, _frame, rcvr, args):
        return self._do_if(rcvr, args[0])

    def _do_if(self, rcvr, branch):
        if rcvr is self._condition:
            if isinstance(branch, AstBlock):
                return branch.get_method().invoke_1(branch)
            return branch
        assert rcvr is falseObject or rcvr is trueObject
        return nilObject

    @staticmethod
    def can_specialize(selector, rcvr, args, _node):
        sel = selector.get_embedded_string()
        return (
            len(args) == 1
            and (rcvr is trueObject or rcvr is falseObject)
            and (sel == "ifTrue:" or sel == "ifFalse:")
        )

    @staticmethod
    def specialize_node(selector, _rcvr, _args, node):
        if selector.get_embedded_string() == "ifTrue:":
            return node.replace(
                IfNode(
                    node._rcvr_expr,  # pylint: disable=protected-access
                    node._arg_exprs[0],  # pylint: disable=protected-access
                    trueObject,
                    node.universe,
                    node.source_section,
                )
            )
        assert selector.get_embedded_string() == "ifFalse:"
        return node.replace(
            IfNode(
                node._rcvr_expr,  # pylint: disable=protected-access
                node._arg_exprs[0],  # pylint: disable=protected-access
                falseObject,
                node.universe,
                node.source_section,
            )
        )
