from som.interpreter.ast.frame import read_frame
from som.interpreter.ast.nodes.contextual_node import ContextualNode
from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.interpreter.ast.nodes.field_node import FieldReadNode
from som.interpreter.ast.nodes.literal_node import LiteralNode
from som.interpreter.ast.nodes.message.generic_node import BinarySend
from som.interpreter.ast.nodes.variable_node import LocalFrameVarReadNode, NonLocalVariableReadNode
from som.vm.globals import trueObject, falseObject, nilObject
from som.vm.symbols import symbol_for
from som.vmobjects.string import String


class LocalFieldStringEqualsNode(ExpressionNode):
    _immutable_fields_ = ["_field_idx", "_frame_idx", "_str", "_universe"]

    def __init__(self, field_idx, frame_idx, str_obj, universe, source_section):
        ExpressionNode.__init__(self, source_section)
        self._field_idx = field_idx
        self._frame_idx = frame_idx
        self._str = str_obj
        self._universe = universe

    def execute(self, frame):
        self_obj = read_frame(frame, self._frame_idx)
        field_val = self_obj.get_field(self._field_idx)

        if isinstance(field_val, String):
            if field_val.get_embedded_string() == self._str:
                return trueObject
            return falseObject

        if field_val is nilObject:
            return falseObject

        return self._make_generic_send(self_obj)

    def _make_generic_send(self, receiver):
        str_obj = String(self._str)
        node = BinarySend(symbol_for("="),
                          self._universe,
                          FieldReadNode(
                              LocalFrameVarReadNode(self._frame_idx, self.source_section),
                              self._field_idx,
                              self.source_section),
                          LiteralNode(str_obj, self.source_section),
                          self.source_section)
        self.replace(node)
        return node.exec_evaluated_2(receiver, str_obj)

    def handle_inlining(self, mgenc):
        assert False

    def handle_outer_inlined(
        self, removed_ctx_level, mgenc_with_inlined
    ):
        assert False


class NonLocalFieldStringEqualsNode(ContextualNode):
    def __init__(self, field_idx, frame_idx, ctx_level, str_obj, universe, source_section):
        ContextualNode.__init__(self, ctx_level, source_section)
        self._field_idx = field_idx
        self._frame_idx = frame_idx
        self._str = str_obj
        self._universe = universe

    def execute(self, frame):
        self_obj = self.determine_outer_self(frame)
        field_val = self_obj.get_field(self._field_idx)

        if isinstance(field_val, String):
            if field_val.get_embedded_string() == self._str:
                return trueObject
            return falseObject

        if field_val is nilObject:
            return falseObject

        return self._make_generic_send(self_obj)

    def handle_inlining(self, mgenc):
        self._context_level -= 1
        if self._context_level == 0:
            node = LocalFieldStringEqualsNode(
                self._field_idx, self._frame_idx, self._str, self._universe, self.source_section)
            self.replace(node)

    def handle_outer_inlined(
        self, removed_ctx_level, mgenc_with_inlined
    ):
        assert (
                self._context_level > removed_ctx_level
        ), "TODO: do I need to think about this more?"
        self._context_level -= 1
        assert (
                self._context_level > 0
        ), "This should remain true, because a block enclosing this one got inlined somewhere"

    def _make_generic_send(self, receiver):
        str_obj = String(self._str)
        node = BinarySend(symbol_for("="),
                          self._universe,
                          FieldReadNode(
                              NonLocalVariableReadNode(self._context_level, self._frame_idx, self.source_section),
                              self._field_idx,
                              self.source_section),
                          LiteralNode(str_obj, self.source_section),
                          self.source_section)
        self.replace(node)
        return node.exec_evaluated_2(receiver, str_obj)
