from rlib.debug import make_sure_not_resized


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

    def add_inlined_locals(self, local_vars):
        if not local_vars:
            return

        combined = [None] * (len(self.locals) + len(local_vars))

        i = 0
        for local in self.locals:
            combined[i] = local
            i += 1

        for local in local_vars:
            combined[i] = local
            i += 1

        self.locals = combined
        make_sure_not_resized(self.locals)

    def drop_inlined_scope(self):
        """
        This removes the inlined scope from the chain.
        Removal is done exactly once, after all embedded blocks
        were adapted.
        """
        assert self.outer.outer
        self.outer = self.outer.outer
