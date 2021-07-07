from rlib.debug import make_sure_not_resized
from rtruffle.node import Node

from som.interpreter.ast.frame import create_frame


class Invokable(Node):

    _immutable_fields_ = [
        "_expr_or_sequence?",
        "_arg_inner_access[*]",
        "_size_frame",
        "_size_inner",
    ]
    _child_nodes_ = ["_expr_or_sequence"]

    def __init__(
        self,
        source_section,
        expr_or_sequence,
        arg_inner_access,
        size_frame,
        size_inner,
    ):
        Node.__init__(self, source_section)
        self._expr_or_sequence = self.adopt_child(expr_or_sequence)
        assert isinstance(arg_inner_access, list)
        make_sure_not_resized(arg_inner_access)

        self._arg_inner_access = arg_inner_access
        self._size_frame = size_frame
        self._size_inner = size_inner

    def invoke(self, receiver, arguments):
        frame = create_frame(
            receiver,
            arguments,
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
        )
        return self._expr_or_sequence.execute(frame)
