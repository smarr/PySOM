from som.interpreter.ast.frame import read_frame
from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.literal_node import LiteralNode
from som.interpreter.ast.nodes.message.generic_node import BinarySend
from som.interpreter.ast.nodes.variable_node import LocalFrameVarReadNode
from som.vm.globals import falseObject, trueObject
from som.vm.symbols import symbol_for
from som.vmobjects.integer import Integer


class LocalFrameIntGreaterThanNode(LocalFrameVarReadNode):
    _immutable_fields_ = ["_value"]

    def __init__(self, val, frame_idx, source_section):
        LocalFrameVarReadNode.__init__(self, frame_idx, source_section)
        self._value = val

    def execute(self, frame):
        arg_val = read_frame(frame, self._frame_idx)
        if isinstance(arg_val, Integer):
            if arg_val.get_embedded_integer() > self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(arg_val)

    def _make_generic_send(self, receiver):
        from som.vm.current import current_universe

        int_val = Integer(self._value)
        literal = LiteralNode(int_val, self.source_section)
        read = LocalFrameVarReadNode(self._frame_idx, self.source_section)

        node = BinarySend(
            symbol_for(">"),
            current_universe,
            read,
            literal,
            self.source_section,
        )

        self.replace(node)
        return node.exec_evaluated_2(receiver, int_val)


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


class LocalFrameIntLessThanNode(LocalFrameVarReadNode):
    _immutable_fields_ = ["_value"]

    def __init__(self, val, frame_idx, source_section):
        LocalFrameVarReadNode.__init__(self, frame_idx, source_section)
        self._value = val

    def execute(self, frame):
        arg_val = read_frame(frame, self._frame_idx)
        if isinstance(arg_val, Integer):
            if arg_val.get_embedded_integer() < self._value:
                return trueObject
            return falseObject

        return self._make_generic_send(arg_val)

    def _make_generic_send(self, receiver):
        from som.vm.current import current_universe

        int_val = Integer(self._value)
        literal = LiteralNode(int_val, self.source_section)
        read = LocalFrameVarReadNode(self._frame_idx, self.source_section)

        node = BinarySend(
            symbol_for("<"),
            current_universe,
            read,
            literal,
            self.source_section,
        )

        self.replace(node)
        return node.exec_evaluated_2(receiver, int_val)


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
