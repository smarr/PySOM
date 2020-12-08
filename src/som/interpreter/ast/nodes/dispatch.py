from rlib import jit

from rtruffle.node import Node


class _AbstractDispatchNode(Node):

    INLINE_CACHE_SIZE = 6

    _immutable_fields_ = ['_universe']

    def __init__(self, universe):
        Node.__init__(self, None)
        self._universe = universe


class _AbstractDispatchWithLookupNode(_AbstractDispatchNode):

    _immutable_fields_ = ['_selector']

    def __init__(self, selector, universe):
        _AbstractDispatchNode.__init__(self, universe)
        self._selector = selector


class UninitializedDispatchNode(_AbstractDispatchWithLookupNode):

    def _specialize(self, rcvr):
        assert rcvr is not None

        # Determine position in dispatch node chain, i.e., size of inline cache
        i_node = self
        chain_depth = 0

        while isinstance(i_node.get_parent(), _AbstractDispatchNode):
            i_node = i_node.get_parent()
            chain_depth += 1

        send_node = i_node.get_parent()

        if chain_depth < _AbstractDispatchNode.INLINE_CACHE_SIZE:
            rcvr_class = rcvr.get_class(self._universe)
            method = rcvr_class.lookup_invokable(self._selector)

            new_chain_end = UninitializedDispatchNode(self._selector,
                                                      self._universe)

            if method is not None:
                node = _CachedDispatchObjectCheckNode(rcvr_class, method,
                                                      new_chain_end,
                                                      self._universe)
            else:
                node = _CachedDnuObjectCheckNode(self._selector, rcvr_class,
                                                 new_chain_end, self._universe)

            return self.replace(node)
        else:
            # the chain is longer than the maximum defined by INLINE_CACHE_SIZE
            # and thus, this callsite is considered to be megaprophic, and we
            # generalize it.

            generic_replacement = GenericDispatchNode(self._selector,
                                                      self._universe)
            send_node.replace_dispatch_list_head(generic_replacement)
            return generic_replacement

    def execute_dispatch(self, rcvr, args):
        return self._specialize(rcvr).execute_dispatch(rcvr, args)


class GenericDispatchNode(_AbstractDispatchWithLookupNode):

    def _lookup_method(self, rcvr):
        return rcvr.get_class(self._universe).lookup_invokable(self._selector)

    def execute_dispatch(self, rcvr, args):
        method = self._lookup_method(rcvr)
        if method is not None:
            return method.invoke(rcvr, args)
        else:
            # Won't use DNU caching here, because it's a megamorphic node
            return send_does_not_understand(rcvr, self._selector, args, self._universe)


class _AbstractCachedDispatchNode(_AbstractDispatchNode):

    _immutable_fields_ = ['_cached_method', '_next?', '_expected_class']
    _child_nodes_      = ['_next']

    def __init__(self, rcvr_class, method, next_dispatch, universe):
        _AbstractDispatchNode.__init__(self, universe)
        self._cached_method  = method
        self._next           = self.adopt_child(next_dispatch)
        self._expected_class = rcvr_class


class _CachedDispatchObjectCheckNode(_AbstractCachedDispatchNode):

    def execute_dispatch(self, rcvr, args):
        if rcvr.get_class(self._universe) == self._expected_class:
            return self._cached_method.invoke(rcvr, args)
        else:
            return self._next.execute_dispatch(rcvr, args)


class _CachedDnuObjectCheckNode(_AbstractCachedDispatchNode):

    _immutable_fields_ = ['_selector']

    def __init__(self, selector, rcvr_class, next_dispatch, universe):
        _AbstractCachedDispatchNode.__init__(
            self, rcvr_class, rcvr_class.lookup_invokable(
                universe.symbol_for("doesNotUnderstand:arguments:")),
            next_dispatch, universe)
        self._selector = selector

    def execute_dispatch(self, rcvr, args):
        if rcvr.get_class(self._universe) == self._expected_class:
            return self._cached_method.invoke(
                rcvr, [self._selector,
                       self._universe.new_array_from_list(args)])
        else:
            return self._next.execute_dispatch(rcvr, args)


class SuperDispatchNode(_AbstractDispatchNode):

    _immutable_fields_ = ['_cached_method']

    def __init__(self, selector, lookup_class, universe):
        _AbstractDispatchNode.__init__(self, universe)
        self._cached_method = lookup_class.lookup_invokable(selector)
        if self._cached_method is None:
            raise RuntimeError("#dnu support for super missing")

    def execute_dispatch(self, rcvr, args):
        return self._cached_method.invoke(rcvr, args)


# @jit.unroll_safe
def _prepare_dnu_arguments(arguments, selector, universe):
    # Compute the number of arguments
    selector = jit.promote(selector)
    universe = jit.promote(universe)
    number_of_arguments = selector.get_number_of_signature_arguments() - 1  # without self
    assert number_of_arguments == len(arguments)

    # TODO: make sure this is still optimizing DNU properly
    # don't want to see any overhead just for using strategies
    arguments_array = universe.new_array_from_list(arguments)
    args = [selector, arguments_array]
    return args


def send_does_not_understand(receiver, selector, arguments, universe):
    args = _prepare_dnu_arguments(arguments, selector, universe)
    return lookup_and_send(receiver, "doesNotUnderstand:arguments:", args, universe)


def lookup_and_send(receiver, selector_string, arguments, universe):
    selector = universe.symbol_for(selector_string)
    invokable = receiver.get_class(universe).lookup_invokable(selector)
    return invokable.invoke(receiver, arguments)

