from som.interpreter.ast.nodes.expression_node import ExpressionNode


class AbstractSuperMessageNode(ExpressionNode):
    _immutable_fields_ = ["_method?", "_super_class", "_selector", "_rcvr_expr?"]
    _child_nodes_ = ["_rcvr_expr"]

    def __init__(self, selector, rcvr_expr, super_class, source_section=None):
        ExpressionNode.__init__(self, source_section)
        self._selector = selector

        self._method = None
        self._super_class = super_class
        self._selector = selector
        self._rcvr_expr = self.adopt_child(rcvr_expr)


class UnarySuper(AbstractSuperMessageNode):
    def execute(self, frame):
        if self._method is None:
            self._method = self._super_class.lookup_invokable(self._selector)
            if not self._method:
                raise Exception("Not yet implemented")

        rcvr = self._rcvr_expr.execute(frame)
        return self._method.invoke_1(rcvr)


class BinarySuper(AbstractSuperMessageNode):
    _immutable_fields_ = ["_arg_expr?"]
    _child_nodes_ = ["_arg_expr"]

    def __init__(self, selector, rcvr_expr, arg_expr, super_class, source_section=None):
        AbstractSuperMessageNode.__init__(
            self, selector, rcvr_expr, super_class, source_section
        )
        self._arg_expr = self.adopt_child(arg_expr)

    def execute(self, frame):
        if self._method is None:
            self._method = self._super_class.lookup_invokable(self._selector)
            if not self._method:
                raise Exception("Not yet implemented")

        rcvr = self._rcvr_expr.execute(frame)
        arg = self._arg_expr.execute(frame)
        return self._method.invoke_2(rcvr, arg)


class TernarySuper(AbstractSuperMessageNode):
    _immutable_fields_ = ["_arg1_expr?", "_arg2_expr?"]
    _child_nodes_ = ["_arg1_expr", "_arg2_expr"]

    def __init__(
        self,
        selector,
        rcvr_expr,
        arg1_expr,
        arg2_expr,
        super_class,
        source_section=None,
    ):
        AbstractSuperMessageNode.__init__(
            self, selector, rcvr_expr, super_class, source_section
        )
        self._arg1_expr = self.adopt_child(arg1_expr)
        self._arg2_expr = self.adopt_child(arg2_expr)

    def execute(self, frame):
        if self._method is None:
            self._method = self._super_class.lookup_invokable(self._selector)
            if not self._method:
                raise Exception("Not yet implemented")

        rcvr = self._rcvr_expr.execute(frame)
        arg1 = self._arg1_expr.execute(frame)
        arg2 = self._arg2_expr.execute(frame)
        return self._method.invoke_3(rcvr, arg1, arg2)


class NArySuper(AbstractSuperMessageNode):
    _immutable_fields_ = ["_arg_exprs?[*]"]
    _child_nodes_ = ["_arg_exprs[*]"]

    def __init__(
        self, selector, rcvr_expr, arg_exprs, super_class, source_section=None
    ):
        AbstractSuperMessageNode.__init__(
            self, selector, rcvr_expr, super_class, source_section
        )
        assert len(arg_exprs) > 2
        self._arg_exprs = self.adopt_children(arg_exprs)

    def execute(self, frame):
        if self._method is None:
            self._method = self._super_class.lookup_invokable(self._selector)
            if not self._method:
                raise Exception("Not yet implemented")

        rcvr = self._rcvr_expr.execute(frame)
        args = [arg_exp.execute(frame) for arg_exp in self._arg_exprs]
        return self._method.invoke_args(rcvr, args)
