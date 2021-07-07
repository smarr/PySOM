from rlib import jit

from rtruffle.node import Node
from som.vmobjects.array import Array


INLINE_CACHE_SIZE = 6


class _AbstractDispatchNode(Node):

    _immutable_fields_ = ["expected_class", "next_entry?"]
    _child_nodes_ = ["next_entry"]

    def __init__(self, expected_class, next_entry):
        Node.__init__(self, None)
        self.expected_class = expected_class
        self.next_entry = self.adopt_child(next_entry)


class GenericDispatchNode(_AbstractDispatchNode):
    _immutable_fields_ = ["universe", "_selector"]

    def __init__(self, selector, universe):
        """
        The Generic Dispatch Node sets expected_class to None.
        This is used as a check in the dispatch, to recognize the generic case.
        """
        _AbstractDispatchNode.__init__(self, None, None)
        self.universe = universe
        self._selector = selector

    def execute_dispatch(self, rcvr, args):
        method = rcvr.get_class(self.universe).lookup_invokable(self._selector)
        if method is not None:
            return method.invoke(rcvr, args)
        # Won't use DNU caching here, because it's a megamorphic node
        return send_does_not_understand(rcvr, self._selector, args, self.universe)


class CachedDispatchNode(_AbstractDispatchNode):

    _immutable_fields_ = ["_cached_method"]

    def __init__(self, rcvr_class, method, next_entry):
        _AbstractDispatchNode.__init__(self, rcvr_class, next_entry)
        self._cached_method = method

    def execute_dispatch(self, rcvr, args):
        return self._cached_method.invoke(rcvr, args)


class CachedDnuNode(_AbstractDispatchNode):

    _immutable_fields_ = ["_selector", "_cached_method"]

    def __init__(self, selector, rcvr_class, next_entry, universe):
        _AbstractDispatchNode.__init__(
            self,
            rcvr_class,
            next_entry,
        )
        self._selector = selector
        self._cached_method = rcvr_class.lookup_invokable(
            universe.symbol_for("doesNotUnderstand:arguments:")
        )

    def execute_dispatch(self, rcvr, args):
        return self._cached_method.invoke(
            rcvr, [self._selector, Array.from_values(args)]
        )


# @jit.unroll_safe
def _prepare_dnu_arguments(arguments, selector, universe):
    # Compute the number of arguments
    selector = jit.promote(selector)
    universe = jit.promote(universe)
    number_of_arguments = (
        selector.get_number_of_signature_arguments() - 1
    )  # without self
    assert number_of_arguments == len(arguments)

    # TODO: make sure this is still optimizing DNU properly
    # don't want to see any overhead just for using strategies
    arguments_array = Array.from_values(arguments)
    args = [selector, arguments_array]
    return args


def send_does_not_understand(receiver, selector, arguments, universe):
    args = _prepare_dnu_arguments(arguments, selector, universe)
    return lookup_and_send(receiver, "doesNotUnderstand:arguments:", args, universe)


def lookup_and_send(receiver, selector_string, arguments, universe):
    selector = universe.symbol_for(selector_string)
    invokable = receiver.get_class(universe).lookup_invokable(selector)
    return invokable.invoke(receiver, arguments)
