from som.interpreter.ast.frame import read_frame
from som.interpreter.ast.nodes.message.generic_node import _AbstractGenericMessageNode


class UnaryArgSend(_AbstractGenericMessageNode):
    _immutable_fields_ = ["_frame_idx"]

    def __init__(self, selector, universe, frame_idx, source_section=None):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, None, source_section
        )
        self._frame_idx = frame_idx

    def execute(self, frame):
        rcvr = read_frame(frame, self._frame_idx)
        return self.exec_evaluated_1(rcvr)

    def execute_evaluated(self, _frame, rcvr, _args):
        return self.exec_evaluated_1(rcvr)

    def exec_evaluated_1(self, rcvr):
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_1(rcvr)


class BinaryArgSend(_AbstractGenericMessageNode):
    _immutable_fields_ = ["_frame_idx"]

    def __init__(self, selector, universe, frame_idx, arg_expr, source_section=None):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, arg_expr, source_section
        )
        self._frame_idx = frame_idx

    def execute(self, frame):
        rcvr = read_frame(frame, self._frame_idx)
        arg = self._rcvr_expr.execute(frame)
        return self.exec_evaluated_2(rcvr, arg)

    def execute_evaluated(self, _frame, rcvr, args):
        return self.exec_evaluated_2(rcvr, args[0])

    def exec_evaluated_2(self, rcvr, arg):
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_2(rcvr, arg)


class TernaryArgSend(_AbstractGenericMessageNode):
    _immutable_fields_ = ["_frame_idx", "_arg2_expr?"]
    _child_nodes_ = ["_arg2_expr"]

    def __init__(
        self, selector, universe, frame_idx, arg1_expr, arg2_expr, source_section=None
    ):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, arg1_expr, source_section
        )
        self._frame_idx = frame_idx
        self._arg2_expr = self.adopt_child(arg2_expr)

    def execute(self, frame):
        rcvr = read_frame(frame, self._frame_idx)
        arg1 = self._rcvr_expr.execute(frame)
        arg2 = self._arg2_expr.execute(frame)
        return self.exec_evaluated_3(rcvr, arg1, arg2)

    def execute_evaluated(self, _frame, rcvr, args):
        return self.exec_evaluated_3(rcvr, args[0], args[1])

    def exec_evaluated_3(self, rcvr, arg1, arg2):
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_3(rcvr, arg1, arg2)
