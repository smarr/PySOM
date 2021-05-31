from .abstract_node import AbstractMessageNode


class SuperMessageNode(AbstractMessageNode):
    def __init__(self, selector, receiver, args, super_class, source_section = None):
        AbstractMessageNode.__init__(self, selector, None, receiver, args, source_section)
        method = super_class.lookup_invokable(selector)
        if not method:
            raise Exception("Not yet implemented")
        self._method = method

    def execute(self, frame):
        rcvr, args = self._evaluate_rcvr_and_args(frame)
        return self._method.invoke(rcvr, args)
