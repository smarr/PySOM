from __future__ import absolute_import

from rlib import jit

from som.vmobjects.abstract_object import AbstractObject


class AstMethod(AbstractObject):

    _immutable_fields_ = ["_signature", "_invokable",
                          "_embedded_block_methods", "_universe", "_holder"]

    def __init__(self, signature, invokable, embedded_block_methods, universe):
        AbstractObject.__init__(self)

        self._signature    = signature
        self._invokable    = invokable

        self._embedded_block_methods = embedded_block_methods
        self._universe = universe

        self._holder   = None

    def get_universe(self):
        return self._universe

    @staticmethod
    def is_primitive():
        return False

    @staticmethod
    def is_invokable():
        """ We use this method to identify methods and primitives """
        return True

    def get_signature(self):
        return self._signature

    def get_holder(self):
        return self._holder

    def set_holder(self, value):
        self._holder = value
        for method in self._embedded_block_methods:
            method.set_holder(value)

    @jit.elidable_promote('all')
    def get_number_of_arguments(self):
        return self.get_signature().get_number_of_signature_arguments()

    def invoke(self, receiver, args):
        return self._invokable.invoke(receiver, args)

    def __str__(self):
        if self._holder:
            holder = self._holder.get_name().get_embedded_string()
        else:
            holder = 'nil'
        return "Method(" + holder + ">>" + str(self.get_signature()) + ")"

    def get_class(self, universe):
        return universe.methodClass

    def merge_point_string(self):
        """ debug info for the jit """
        return "%s>>%s" % (self.get_holder().get_name().get_embedded_string(),
                           self.get_signature().get_embedded_string())
