class LexicalScope(object):
    _immutable_fields_ = ["_outer", "arguments[*]", "locals[*]"]

    def __init__(self, outer, arguments, local_vars):
        self._outer = outer
        self.arguments = arguments
        self.locals = local_vars

    def get_argument(self, idx, ctx_level):
        if ctx_level > 0:
            return self._outer.get_argument(idx, ctx_level - 1)
        return self.arguments[idx]

    def get_local(self, idx, ctx_level):
        if ctx_level > 0:
            return self._outer.get_local(idx, ctx_level - 1)
        return self.locals[idx]
