from rlib.debug import make_sure_not_resized
from rtruffle.node import Node

from som.interpreter.ast.frame import (
    create_frame_1,
    create_frame_2,
    create_frame_args,
    create_frame_3,
)


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

    def invoke_1(self, receiver):
        frame = create_frame_1(
            receiver,
            self._size_frame,
            self._size_inner,
        )
        return self._expr_or_sequence.execute(frame)

    def invoke_2(self, receiver, arg):
        frame = create_frame_2(
            receiver,
            arg,
            self._arg_inner_access[0],
            self._size_frame,
            self._size_inner,
        )
        return self._expr_or_sequence.execute(frame)

    def invoke_3(self, receiver, arg1, arg2):
        frame = create_frame_3(
            receiver,
            arg1,
            arg2,
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
        )
        return self._expr_or_sequence.execute(frame)

    def invoke_args(self, receiver, arguments):
        frame = create_frame_args(
            receiver,
            arguments,
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
        )
        return self._expr_or_sequence.execute(frame)
