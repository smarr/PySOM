from rlib.jit import JitDriver

from som.interpreter.ast.nodes.expression_node import ExpressionNode
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer


class ToDoInlined(ExpressionNode):
    _immutable_fields_ = [
        "_from_expr?",
        "_to_expr?",
        "_do_expr?",
        "_idx_var",
        "_idx_write?",
    ]
    _child_nodes_ = ["_from_expr", "_to_expr", "_do_expr", "_idx_write"]

    def __init__(self, from_expr, to_expr, do_expr, idx_var, source_section):
        ExpressionNode.__init__(self, source_section)
        self._from_expr = self.adopt_child(from_expr)
        self._to_expr = self.adopt_child(to_expr)
        self._do_expr = self.adopt_child(do_expr)
        self._idx_var = idx_var
        self._idx_write = self.adopt_child(idx_var.get_write_node(0, None))

    def execute(self, frame):
        start = self._from_expr.execute(frame)
        assert isinstance(start, Integer)

        end = self._to_expr.execute(frame)
        if isinstance(end, Integer):
            _to_do_int(
                frame,
                start.get_embedded_integer(),
                end.get_embedded_integer(),
                self._idx_write,
                self._do_expr,
            )
            return start

        assert isinstance(end, Double)
        _to_do_dbl(
            frame,
            start.get_embedded_integer(),
            end.get_embedded_double(),
            self._idx_write,
            self._do_expr,
        )
        return start


def get_printable_location(do_expr, idx_write):  # pylint: disable=unused-argument
    assert isinstance(do_expr, ExpressionNode)
    return "#to:do: %s" % str(do_expr.source_section)


int_driver = JitDriver(
    greens=["do_expr", "idx_write"],
    reds="auto",
    is_recursive=True,
    get_printable_location=get_printable_location,
)


dbl_driver = JitDriver(
    greens=["do_expr", "idx_write"],
    reds="auto",
    is_recursive=True,
    get_printable_location=get_printable_location,
)


def _to_do_int(frame, start, end, idx_write, do_expr):
    for i in range(start, end + 1):
        int_driver.jit_merge_point(do_expr=do_expr, idx_write=idx_write)
        idx_write.write_value(frame, Integer(i))
        do_expr.execute(frame)


def _to_do_dbl(frame, start, end, idx_write, do_expr):
    for i in range(start, end + 1):
        dbl_driver.jit_merge_point(do_expr=do_expr, idx_write=idx_write)
        idx_write.write_value(frame, Integer(i))
        do_expr.execute(frame)
