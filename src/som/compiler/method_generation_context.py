class MethodGenerationContextBase(object):

    def __init__(self, universe):
        self._holder_genc  = None
        self._outer_genc   = None
        self._block_method = False
        self._signature    = None
        self._primitive    = False  # to be changed

        self._universe = universe

    def set_holder(self, cgenc):
        self._holder_genc = cgenc

    def set_primitive(self):
        self._primitive = True

    def set_signature(self, sig):
        self._signature = sig

    def set_is_block_method(self, boolean):
        self._block_method = boolean

    def get_holder(self):
        return self._holder_genc

    def set_outer(self, mgenc):
        self._outer_genc = mgenc

    def is_block_method(self):
        return self._block_method

    def has_field(self, field):
        return self._holder_genc.has_field(field)

    def get_field_index(self, field):
        return self._holder_genc.get_field_index(field)

    def get_number_of_arguments(self):
        return len(self._arguments)

    def get_signature(self):
        return self._signature

    def add_local_if_absent(self, local):
        if local in self._locals:
            return False
        self.add_local(local)
        return True
