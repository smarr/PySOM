from rlib.debug import make_sure_not_resized
from rlib.jit import we_are_jitted, elidable_promote

from som.interpreter.ast.nodes.dispatch import (
    send_does_not_understand,
    INLINE_CACHE_SIZE,
    CachedDispatchNode,
    CachedDnuNode,
    GenericDispatchNode,
)
from som.interpreter.ast.nodes.message.abstract_node import AbstractMessageNode


class GenericMessageNode(AbstractMessageNode):

    _immutable_fields_ = ["_dispatch?"]
    _child_nodes_ = ["_dispatch"]

    def __init__(self, selector, universe, rcvr_expr, arg_exprs, source_section=None):
        AbstractMessageNode.__init__(
            self, selector, universe, rcvr_expr, arg_exprs, source_section
        )
        self._dispatch = None

    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self.execute_evaluated(frame, rcvr, args)

    def execute_evaluated(self, frame, rcvr, args):
        assert frame is not None
        assert rcvr is not None
        assert args is not None
        make_sure_not_resized(args)

        rcvr_class = rcvr.get_class(self.universe)

        if we_are_jitted():
            return self._direct_dispatch(rcvr, rcvr_class, args)

        # TODO: remove we_are_jitted() special case
        dispatch_node = self._lookup(rcvr_class)
        return dispatch_node.execute_dispatch(rcvr, args)

    @elidable_promote("all")
    def _lookup(self, rcvr_class):
        first = self._dispatch
        cache = first
        while cache is not None:
            if cache.expected_class is rcvr_class:
                return cache
            cache = cache.next_entry

        # this is the generic dispatch node
        if first and first.expected_class is None:
            return first

        return self._specialize(rcvr_class)

    def _get_cache_size(self):
        size = 0
        cache = self._dispatch
        while cache is not None:
            size += 1
            cache = cache.next_entry
        return size

    def _specialize(self, rcvr_class):
        cache_size = self._get_cache_size()

        if cache_size < INLINE_CACHE_SIZE:
            method = rcvr_class.lookup_invokable(self._selector)

            if method is not None:
                node = CachedDispatchNode(rcvr_class, method, self._dispatch)
            else:
                node = CachedDnuNode(
                    self._selector, rcvr_class, self._dispatch, self.universe
                )

            node.parent = self
            self._dispatch = node
            return node

        # the chain is longer than the maximum defined by INLINE_CACHE_SIZE
        # and thus, this callsite is considered to be megaprophic, and we
        # generalize it.
        generic_replacement = GenericDispatchNode(self._selector, self.universe)
        generic_replacement.parent = self
        self._dispatch = generic_replacement
        return generic_replacement

    def _direct_dispatch(self, rcvr, rcvr_class, args):
        method = rcvr_class.lookup_invokable(self._selector)
        if method:
            return method.invoke(rcvr, args)
        return send_does_not_understand(rcvr, self._selector, args, self.universe)

    def __str__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            self._selector,
            self.source_section,
        )
