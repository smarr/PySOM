from rlib.debug import make_sure_not_resized
from rlib.jit import elidable_promote

from som.interpreter.ast.nodes.dispatch import (
    INLINE_CACHE_SIZE,
    CachedDispatchNode,
    CachedDnuNode,
    GenericDispatchNode,
)
from som.interpreter.ast.nodes.expression_node import ExpressionNode


class _AbstractGenericMessageNode(ExpressionNode):
    _immutable_fields_ = ["_selector", "_dispatch?", "_rcvr_expr?", "universe"]
    _child_nodes_ = ["_rcvr_expr"]

    def __init__(self, selector, universe, rcvr_expr, source_section=None):
        ExpressionNode.__init__(self, source_section)
        self._selector = selector
        self.universe = universe
        self._rcvr_expr = self.adopt_child(rcvr_expr)
        self._dispatch = None

    @elidable_promote("all")
    def _lookup(self, layout):
        first = self._dispatch
        cache = first
        while cache is not None:
            if cache.expected_layout is layout:
                return cache
            cache = cache.next_entry

        # this is the generic dispatch node
        if first and first.expected_layout is None:
            return first

        return None

    def _get_cache_size_and_drop_old_entries(self):
        # Keep in sync with: BcAbstractMethod.drop_old_inline_cache_entries
        size = 0
        prev = None
        cache = self._dispatch
        while cache is not None:
            if not cache.expected_layout.is_latest:
                # drop old layout from cache
                if prev is None:
                    self._dispatch = cache.next_entry
                else:
                    prev.next_entry = cache.next_entry
            else:
                size += 1
                prev = cache

            cache = cache.next_entry
        return size

    def _specialize(self, layout, obj):
        if not layout.is_latest:
            obj.update_layout_to_match_class()
            layout = obj.get_object_layout(self.universe)
            cache = self._lookup(layout)
            if cache is not None:
                return cache

        cache_size = self._get_cache_size_and_drop_old_entries()

        if cache_size < INLINE_CACHE_SIZE:
            method = layout.lookup_invokable(self._selector)

            if method is not None:
                node = CachedDispatchNode(layout, method, self._dispatch)
            else:
                node = CachedDnuNode(self._selector, layout, self._dispatch)

            node.parent = self
            self._dispatch = node
            return node

        # the chain is longer than the maximum defined by INLINE_CACHE_SIZE
        # and thus, this callsite is considered to be megamorphic, and we
        # generalize it.
        generic_replacement = GenericDispatchNode(self._selector, self.universe)
        generic_replacement.parent = self
        self._dispatch = generic_replacement
        return generic_replacement

    def __str__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            self._selector,
            self.source_section,
        )


class UnarySend(_AbstractGenericMessageNode):
    def __init__(self, selector, universe, rcvr_expr, source_section=None):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, rcvr_expr, source_section
        )

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_1(rcvr)

    def execute_evaluated(self, _frame, rcvr, _args):
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_1(rcvr)


class BinarySend(_AbstractGenericMessageNode):
    _immutable_fields_ = ["_arg_expr?"]
    _child_nodes_ = ["_arg_expr"]

    def __init__(self, selector, universe, rcvr_expr, arg_expr, source_section=None):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, rcvr_expr, source_section
        )
        self._arg_expr = self.adopt_child(arg_expr)

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        arg = self._arg_expr.execute(frame)
        return self.exec_evaluated_2(rcvr, arg)

    def execute_evaluated(self, _frame, rcvr, args):
        return self.exec_evaluated_2(rcvr, args[0])

    def exec_evaluated_2(self, rcvr, arg):
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_2(rcvr, arg)


class TernarySend(_AbstractGenericMessageNode):
    _immutable_fields_ = ["_arg1_expr?", "_arg2_expr?"]
    _child_nodes_ = ["_arg1_expr", "_arg2_expr"]

    def __init__(
        self, selector, universe, rcvr_expr, arg1_expr, arg2_expr, source_section=None
    ):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, rcvr_expr, source_section
        )
        self._arg1_expr = self.adopt_child(arg1_expr)
        self._arg2_expr = self.adopt_child(arg2_expr)

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        arg1 = self._arg1_expr.execute(frame)
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


class NArySend(_AbstractGenericMessageNode):
    _immutable_fields_ = ["_arg_exprs?[*]"]
    _child_nodes_ = ["_arg_exprs[*]"]

    def __init__(self, selector, universe, rcvr_expr, arg_exprs, source_section=None):
        _AbstractGenericMessageNode.__init__(
            self, selector, universe, rcvr_expr, source_section
        )
        self._arg_exprs = self.adopt_children(arg_exprs)
        make_sure_not_resized(self._arg_exprs)

    def execute(self, frame):
        rcvr = self._rcvr_expr.execute(frame)
        args = [arg_exp.execute(frame) for arg_exp in self._arg_exprs]
        return self.execute_evaluated(None, rcvr, args)

    def execute_evaluated(self, _frame, rcvr, args):
        layout = rcvr.get_object_layout(self.universe)
        dispatch_node = self._lookup(layout)
        if dispatch_node is None:
            dispatch_node = self._specialize(layout, rcvr)
        return dispatch_node.dispatch_args(rcvr, args)
