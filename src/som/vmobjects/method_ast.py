from __future__ import absolute_import

from rlib import jit

from som.vmobjects.method import AbstractMethod


class AstMethod(AbstractMethod):

    _immutable_fields_ = [
        "_invokable",
        "_embedded_block_methods",
    ]

    def __init__(self, signature, invokable, embedded_block_methods):
        AbstractMethod.__init__(self, signature)
        self._invokable = invokable
        self._embedded_block_methods = embedded_block_methods

    def set_holder(self, value):
        self._holder = value
        for method in self._embedded_block_methods:
            method.set_holder(value)

    @jit.elidable_promote("all")
    def get_number_of_arguments(self):
        return self.get_signature().get_number_of_signature_arguments()

    def invoke(self, receiver, args):
        return self._invokable.invoke(receiver, args)
