from __future__ import absolute_import

from rlib import jit
from rlib.debug import make_sure_not_resized

from som.vmobjects.method import AbstractMethod


def get_printable_location(self):
    return self._invokable.source_section.identifier


jitdriver = jit.JitDriver(
    greens=["self"],
    # virtualizables=["frame"],
    get_printable_location=get_printable_location,
    reds=["arguments", "receiver"],
    is_recursive=True,
    # the next line is a workaround around a likely bug in RPython
    # for some reason, the inlining heuristics default to "never inline" when
    # two different jit drivers are involved (in our case, the primitive
    # driver, and this one).
    # the next line says that calls involving this jitdriver should always be
    # inlined once (which means that things like Integer>>< will be inlined
    # into a while loop again, when enabling this driver).
    should_unroll_one_iteration=lambda self: True,
)


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
        assert args is not None
        make_sure_not_resized(args)

        jitdriver.jit_merge_point(self=self, receiver=receiver, arguments=args)

        return self._invokable.invoke(receiver, args)
