from __future__ import absolute_import

from rlib import jit
from rlib.debug import make_sure_not_resized

from som.vmobjects.method import AbstractMethod


def get_printable_location_1(self):
    assert isinstance(self, AstMethod)
    return self._invokable.source_section.identifier  # pylint: disable=protected-access


def get_printable_location_2(self):
    assert isinstance(self, AstMethod)
    return self._invokable.source_section.identifier  # pylint: disable=protected-access


def get_printable_location_3(self):
    assert isinstance(self, AstMethod)
    return self._invokable.source_section.identifier  # pylint: disable=protected-access


def get_printable_location_args(self):
    assert isinstance(self, AstMethod)
    return self._invokable.source_section.identifier  # pylint: disable=protected-access


jitdriver_1 = jit.JitDriver(
    greens=["self"],
    get_printable_location=get_printable_location_1,
    reds=["rcvr"],
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

jitdriver_2 = jit.JitDriver(
    greens=["self"],
    get_printable_location=get_printable_location_2,
    reds=["rcvr", "arg"],
    is_recursive=True,
    should_unroll_one_iteration=lambda self: True,
)

jitdriver_3 = jit.JitDriver(
    greens=["self"],
    get_printable_location=get_printable_location_3,
    reds=["rcvr", "arg1", "arg2"],
    is_recursive=True,
    should_unroll_one_iteration=lambda self: True,
)

jitdriver_args = jit.JitDriver(
    greens=["self"],
    get_printable_location=get_printable_location_args,
    reds=["rcvr", "args"],
    is_recursive=True,
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

    def invoke_1(self, rcvr):
        jitdriver_1.jit_merge_point(self=self, rcvr=rcvr)
        return self._invokable.invoke_1(rcvr)

    def invoke_2(self, rcvr, arg):
        jitdriver_2.jit_merge_point(self=self, rcvr=rcvr, arg=arg)
        return self._invokable.invoke_2(rcvr, arg)

    def invoke_3(self, rcvr, arg1, arg2):
        jitdriver_3.jit_merge_point(self=self, rcvr=rcvr, arg1=arg1, arg2=arg2)
        return self._invokable.invoke_3(rcvr, arg1, arg2)

    def invoke_args(self, rcvr, args):
        assert args is not None
        make_sure_not_resized(args)

        jitdriver_args.jit_merge_point(self=self, rcvr=rcvr, args=args)
        return self._invokable.invoke_args(rcvr, args)
