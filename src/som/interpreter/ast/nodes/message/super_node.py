from .abstract_node import AbstractMessageNode


class SuperMessageNode(AbstractMessageNode):

    _immutable_fields_ = ["_method?", "_super_class", "_selector"]

    def __init__(self, selector, receiver, args, super_class, source_section=None):
        AbstractMessageNode.__init__(
            self, selector, None, receiver, args, source_section
        )
        self._method = None
        self._super_class = super_class
        self._selector = selector

    def execute(self, frame):
        if self._method is None:
            method = self._super_class.lookup_invokable(self._selector)
            if not method:
                raise Exception("Not yet implemented")
            self._method = method

        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self._method.invoke(rcvr, args)
