class LexicalScope(object):
    _immutable_fields_ = ["outer", "arguments[*]", "locals[*]"]

    def __init__(self, outer, arguments, local_vars):
        self.outer = outer
        self.arguments = arguments
        self.locals = local_vars
        assert self.locals is not None
        assert self.arguments is not None

    def get_argument(self, idx, ctx_level):
        if ctx_level > 0:
            return self.outer.get_argument(idx, ctx_level - 1)
        return self.arguments[idx]

    def get_local(self, idx, ctx_level):
        assert self.locals is not None
        if ctx_level > 0:
            return self.outer.get_local(idx, ctx_level - 1)
        return self.locals[idx]
