from rlib import jit
from rlib.debug import make_sure_not_resized
from rtruffle.node import Node

from som.interpreter.ast.frame import create_frame


def get_printable_location(invokable):
    return invokable.source_section.identifier


jitdriver = jit.JitDriver(
    greens=["self"],
    # virtualizables=["frame"],
    get_printable_location=get_printable_location,
    reds=["arguments", "receiver", "frame"],
    is_recursive=True,
    # the next line is a workaround around a likely bug in RPython
    # for some reason, the inlining heuristics default to "never inline" when
    # two different jit drivers are involved (in our case, the primitive
    # driver, and this one).
    # the next line says that calls involving this jitdriver should always be
    # inlined once (which means that things like Integer>>< will be inlined
    # into a while loop again, when enabling this driver).
    should_unroll_one_iteration=lambda self: True,
)


class Invokable(Node):

    _immutable_fields_ = [
        "_expr_or_sequence?",
        "universe",
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
        universe,
    ):
        Node.__init__(self, source_section)
        self._expr_or_sequence = self.adopt_child(expr_or_sequence)
        self.universe = universe
        assert isinstance(arg_inner_access, list)
        make_sure_not_resized(arg_inner_access)

        self._arg_inner_access = arg_inner_access
        self._size_frame = size_frame
        self._size_inner = size_inner

    def invoke(self, receiver, arguments):
        assert arguments is not None
        make_sure_not_resized(arguments)

        frame = create_frame(
            receiver,
            arguments,
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
        )
        jitdriver.jit_merge_point(
            self=self, receiver=receiver, arguments=arguments, frame=frame
        )

        return self._expr_or_sequence.execute(frame)
