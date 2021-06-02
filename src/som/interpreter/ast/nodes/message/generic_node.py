from rlib.debug import make_sure_not_resized
from rlib.jit import we_are_jitted

from ..dispatch import UninitializedDispatchNode, send_does_not_understand
from .abstract_node import AbstractMessageNode


class GenericMessageNode(AbstractMessageNode):

    _immutable_fields_ = ['_dispatch?']
    _child_nodes_      = ['_dispatch']

    def __init__(self, selector, universe, rcvr_expr, arg_exprs,
                 source_section = None):
        AbstractMessageNode.__init__(self, selector, universe, rcvr_expr,
                                     arg_exprs, source_section)
        dispatch = UninitializedDispatchNode(selector, universe)
        self._dispatch = self.adopt_child(dispatch)

    def replace_dispatch_list_head(self, node):
        self._dispatch.replace(node)

    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self.execute_evaluated(frame, rcvr, args)

    def execute_evaluated(self, frame, rcvr, args):
        assert frame is not None
        assert rcvr is not None
        assert args is not None
        make_sure_not_resized(args)
        if we_are_jitted():
            return self._direct_dispatch(rcvr, args)
        else:
            return self._dispatch.execute_dispatch(rcvr, args)

    def _direct_dispatch(self, rcvr, args):
        rcvr_class = rcvr.get_class(self.universe)
        method = rcvr_class.lookup_invokable(self._selector)
        if method:
            return method.invoke(rcvr, args)
        else:
            return send_does_not_understand(rcvr, self._selector, args, self.universe)

    def __str__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               self._selector,
                               self.source_section)
