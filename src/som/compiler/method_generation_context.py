class MethodGenerationContextBase(object):

    def __init__(self, universe, outer = None):
        self.holder  = None
        self._outer_genc   = outer
        self.is_block_method = outer is not None
        self._signature    = None
        self._primitive    = False  # to be changed

        self.universe = universe

    def set_primitive(self):
        self._primitive = True

    def set_signature(self, sig):
        self._signature = sig

    def has_field(self, field):
        return self.holder.has_field(field)

    def get_field_index(self, field):
        return self.holder.get_field_index(field)

    def get_number_of_arguments(self):
        return len(self._arguments)

    def get_signature(self):
        return self._signature

    def add_local_if_absent(self, local):
        if local in self._locals:
            return False
        self.add_local(local)
        return True
