from rlib.debug import make_sure_not_resized
from rlib.jit   import unroll_safe

from ..expression_node import ExpressionNode

from .....vmobjects.abstract_object import AbstractObject


class AbstractMessageNode(ExpressionNode):

    _immutable_fields_ = ['_selector', '_universe',
                          '_rcvr_expr?', '_arg_exprs?[*]']
    _child_nodes_      = ['_rcvr_expr',  '_arg_exprs[*]']

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 source_section = None):
        ExpressionNode.__init__(self, source_section)
        self._selector = selector
        self._universe = universe
        assert arg_exprs is not None
        make_sure_not_resized(arg_exprs)
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._arg_exprs = self.adopt_children(arg_exprs)

    @unroll_safe
    def _evaluate_rcvr_and_args(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        assert isinstance(rcvr, AbstractObject)
        if len(self._arg_exprs) == 0:
            args = []
        else:
            args = [arg_exp.execute(frame) for arg_exp in self._arg_exprs]
        return rcvr, args


