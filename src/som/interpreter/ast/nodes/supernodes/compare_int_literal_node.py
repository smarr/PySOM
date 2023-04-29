from som.interpreter.ast.frame import read_frame, read_inner
from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.literal_node import LiteralNode
from som.interpreter.ast.nodes.message.generic_node import BinarySend
from som.interpreter.ast.nodes.variable_node import (
    LocalFrameVarReadNode,
    LocalInnerVarReadNode,
)
from som.vm.globals import falseObject, trueObject
from som.vm.symbols import symbol_for
from som.vmobjects.integer import Integer


class UninitializedLocalLessOrGreaterThanNode(ExpressionNode):
    _immutable_fields_ = ["_var", "_value"]

    def __init__(self, is_greater_than, var, value, source_section):
        ExpressionNode.__init__(self, source_section)
        self._var = var
        self._is_greater_than = is_greater_than
        self._value = value

    def execute(self, frame):
        return self._specialize().execute(frame)

    def _specialize(self):
        assert self._var.access_idx >= 0
        if self._is_greater_than:
            if self._var.is_accessed_out_of_context():
                node = LocalInnerIntGreaterThanNode(
                    self._value, self._var.access_idx, self.source_section
                )
            else:
                node = LocalFrameIntGreaterThanNode(
                    self._value, self._var.access_idx, self.source_section
                )
        else:
            if self._var.is_accessed_out_of_context():
                node = LocalInnerIntLessThanNode(
                    self._value, self._var.access_idx, self.source_section
                )
            else:
                node = LocalFrameIntLessThanNode(
                    self._value, self._var.access_idx, self.source_section
                )

        return self.replace(node)

    def handle_inlining(self, mgenc):
        from som.compiler.ast.variable import Local

        # we got inlined
        assert isinstance(
            self._var, Local
        ), "We are not currently inlining any blocks with arguments"
        self._var = mgenc.get_inlined_local(self._var, 0)

    def handle_outer_inlined(self, removed_ctx_level, mgenc_with_inlined):
        raise NotImplementedError("TODO: implement me")

    def __str__(self):
        operator = ">" if self._is_greater_than else "<"
        return (
            "UninitializedLocalLessOrGreaterThanNode("
            + str(self._var)
            + ", "
            + operator
            + " "
            + str(self._value)
            + ")"
        )


class _LocalIntNode(ExpressionNode):
    _immutable_fields_ = ["_access_idx", "_value"]

    def __init__(self, value, access_idx, source_section):
        ExpressionNode.__init__(self, source_section)
        self._access_idx = access_idx
        self._value = value

    def _make_read_node(self):
        raise NotImplementedError("Should be overwritten by subclass")

    def _get_operator(self):
        raise NotImplementedError("Should be overwritten by subclass")

    def _make_generic_send(self, receiver):
        from som.vm.current import current_universe

        int_val = Integer(self._value)
        literal = LiteralNode(int_val, self.source_section)
        read = self._make_read_node()

        node = BinarySend(
            symbol_for(self._get_operator()),
            current_universe,
            read,
            literal,
            self.source_section,
        )

        self.replace(node)
        return node.exec_evaluated_2(receiver, int_val)


class LocalFrameIntGreaterThanNode(_LocalIntNode):
    def execute(self, frame):
        arg_val = read_frame(frame, self._access_idx)
        if isinstance(arg_val, Integer):
            if arg_val.get_embedded_integer() > self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(arg_val)

    def _make_read_node(self):
        return LocalFrameVarReadNode(self._access_idx, self.source_section)

    def _get_operator(self):
        return ">"


class LocalInnerIntGreaterThanNode(_LocalIntNode):
    def execute(self, frame):
        arg_val = read_inner(frame, self._access_idx)
        if isinstance(arg_val, Integer):
            if arg_val.get_embedded_integer() > self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(arg_val)

    def _make_read_node(self):
        return LocalInnerVarReadNode(self._access_idx, self.source_section)

    def _get_operator(self):
        return ">"


class GreaterThanIntNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr?", "_value"]
    _child_nodes_ = ["_rcvr"]

    def __init__(self, receiver_expr, int_val, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr = self.adopt_child(receiver_expr)
        self._value = int_val

    def execute(self, frame):
        receiver = self._rcvr.execute(frame)
        if isinstance(receiver, Integer):
            if receiver.get_embedded_integer() > self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(receiver)

    def _make_generic_send(self, receiver):
        from som.vm.current import current_universe

        int_val = Integer(self._value)
        literal = LiteralNode(int_val, self.source_section)

        node = BinarySend(
            symbol_for(">"),
            current_universe,
            self._rcvr,
            literal,
            self.source_section,
        )

        self.replace(node)
        return node.exec_evaluated_2(receiver, int_val)


class LocalFrameIntLessThanNode(_LocalIntNode):
    def execute(self, frame):
        arg_val = read_frame(frame, self._access_idx)
        if isinstance(arg_val, Integer):
            if arg_val.get_embedded_integer() < self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(arg_val)

    def _make_read_node(self):
        return LocalFrameVarReadNode(self._access_idx, self.source_section)

    def _get_operator(self):
        return "<"


class LocalInnerIntLessThanNode(_LocalIntNode):
    def execute(self, frame):
        arg_val = read_inner(frame, self._access_idx)
        if isinstance(arg_val, Integer):
            if arg_val.get_embedded_integer() < self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(arg_val)

    def _make_read_node(self):
        return LocalInnerVarReadNode(self._access_idx, self.source_section)

    def _get_operator(self):
        return "<"


class LessThanIntNode(ExpressionNode):
    _immutable_fields_ = ["_rcvr?", "_value"]
    _child_nodes_ = ["_rcvr"]

    def __init__(self, receiver_expr, int_val, source_section):
        ExpressionNode.__init__(self, source_section)
        self._rcvr = self.adopt_child(receiver_expr)
        self._value = int_val

    def execute(self, frame):
        receiver = self._rcvr.execute(frame)
        if isinstance(receiver, Integer):
            if receiver.get_embedded_integer() < self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(receiver)

    def _make_generic_send(self, receiver):
        from som.vm.current import current_universe

        int_val = Integer(self._value)
        literal = LiteralNode(int_val, self.source_section)

        node = BinarySend(
            symbol_for("<"),
            current_universe,
            self._rcvr,
            literal,
            self.source_section,
        )

        self.replace(node)
        return node.exec_evaluated_2(receiver, int_val)
