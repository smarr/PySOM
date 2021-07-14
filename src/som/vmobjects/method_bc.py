from __future__ import absolute_import

from rlib import jit
from som.interpreter.ast.frame import (
    get_inner_as_context,
    mark_as_no_longer_on_stack,
    FRAME_AND_INNER_RCVR_IDX,
    create_frame_1,
    create_frame_2,
)
from som.interpreter.bc.bytecodes import Bytecodes

from som.interpreter.bc.frame import (
    create_frame,
    stack_pop_old_arguments_and_push_result,
    create_frame_3,
)
from som.interpreter.bc.interpreter import interpret
from som.interpreter.control_flow import ReturnException
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.method import AbstractMethod


class BcAbstractMethod(AbstractMethod):

    _immutable_fields_ = [
        "_bytecodes?[*]",
        "_literals[*]",
        "_inline_cache_class",
        "_inline_cache_invokable",
        "_receiver_class_table",
        "_number_of_locals",
        "_maximum_number_of_stack_elements",
        "_number_of_arguments",
        "_arg_inner_access[*]",
        "_size_frame",
        "_size_inner",
        "_lexical_scope",
    ]

    def __init__(
        self,
        literals,
        num_locals,
        max_stack_elements,
        num_bytecodes,
        signature,
        arg_inner_access,
        size_frame,
        size_inner,
        lexical_scope,
    ):
        AbstractMethod.__init__(self, signature)

        # Set the number of bytecodes in this method
        self._bytecodes = ["\x00"] * num_bytecodes
        self._inline_cache_class = [None] * num_bytecodes
        self._inline_cache_invokable = [None] * num_bytecodes

        self._literals = literals

        self._number_of_arguments = signature.get_number_of_signature_arguments()

        self._number_of_locals = num_locals

        self._maximum_number_of_stack_elements = max_stack_elements + 2

        self._arg_inner_access = arg_inner_access
        self._size_frame = size_frame
        self._size_inner = size_inner

        self._lexical_scope = lexical_scope

    def get_number_of_locals(self):
        return self._number_of_locals

    @jit.elidable_promote("all")
    def get_maximum_number_of_stack_elements(self):
        # Compute the maximum number of stack locations (including
        # extra buffer to support doesNotUnderstand) and set the
        # number of indexable fields accordingly
        return self._maximum_number_of_stack_elements

    def set_holder(self, value):
        self._holder = value

        # Make sure all nested invokables have the same holder
        for obj in self._literals:
            assert isinstance(obj, AbstractObject)
            if obj.is_invokable():
                obj.set_holder(value)

    # XXX this means that the JIT doesn't see changes to the constants
    @jit.elidable_promote("all")
    def get_constant(self, bytecode_index):
        # Get the constant associated to a given bytecode index
        return self._literals[self.get_bytecode(bytecode_index + 1)]

    @jit.elidable_promote("all")
    def get_number_of_arguments(self):
        return self._number_of_arguments

    def get_number_of_signature_arguments(self):
        return self._number_of_arguments

    def get_number_of_bytecodes(self):
        # Get the number of bytecodes in this method
        return len(self._bytecodes)

    @jit.elidable_promote("all")
    def get_bytecode(self, index):
        # Get the bytecode at the given index
        assert 0 <= index < len(self._bytecodes)
        return ord(self._bytecodes[index])

    def set_bytecode(self, index, value):
        # Set the bytecode at the given index to the given value
        assert (
            0 <= value <= 255
        ), "Expected bytecode in the range of [0..255], but was: " + str(value)
        self._bytecodes[index] = chr(value)

    @jit.elidable
    def get_inline_cache_class(self, bytecode_index):
        assert 0 <= bytecode_index < len(self._inline_cache_class)
        return self._inline_cache_class[bytecode_index]

    @jit.elidable
    def get_inline_cache_invokable(self, bytecode_index):
        assert 0 <= bytecode_index < len(self._inline_cache_invokable)
        return self._inline_cache_invokable[bytecode_index]

    def set_inline_cache(self, bytecode_index, receiver_class, invokable):
        self._inline_cache_class[bytecode_index] = receiver_class
        self._inline_cache_invokable[bytecode_index] = invokable

    def patch_variable_access(self, bytecode_index):
        bc = self.get_bytecode(bytecode_index)
        idx = self.get_bytecode(bytecode_index + 1)
        ctx_level = self.get_bytecode(bytecode_index + 2)

        if bc == Bytecodes.push_argument:
            var = self._lexical_scope.get_argument(idx, ctx_level)
            self.set_bytecode(bytecode_index, var.get_push_bytecode())
        elif bc == Bytecodes.pop_argument:
            var = self._lexical_scope.get_argument(idx, ctx_level)
            self.set_bytecode(bytecode_index, var.get_pop_bytecode())
        elif bc == Bytecodes.push_local:
            var = self._lexical_scope.get_local(idx, ctx_level)
            self.set_bytecode(bytecode_index, var.get_push_bytecode())
        elif bc == Bytecodes.pop_local:
            var = self._lexical_scope.get_local(idx, ctx_level)
            self.set_bytecode(bytecode_index, var.get_pop_bytecode())
        else:
            raise Exception("Unsupported bytecode?")
        assert (
            FRAME_AND_INNER_RCVR_IDX <= var.access_idx <= 255
        ), "Expected variable access index to be in valid range, but was " + str(
            var.access_idx
        )
        self.set_bytecode(bytecode_index + 1, var.access_idx)


def _interp_with_nlr(method, new_frame, max_stack_size):
    inner = get_inner_as_context(new_frame)

    try:
        result = interpret(method, new_frame, max_stack_size)
        mark_as_no_longer_on_stack(inner)
        return result
    except ReturnException as e:
        mark_as_no_longer_on_stack(inner)
        if e.has_reached_target(inner):
            return e.get_result()
        raise e


class BcMethod(BcAbstractMethod):
    def invoke_1(self, rcvr):
        new_frame = create_frame_1(rcvr, self._size_frame, self._size_inner)
        return interpret(self, new_frame, self._maximum_number_of_stack_elements)

    def invoke_2(self, rcvr, arg1):
        new_frame = create_frame_2(
            rcvr,
            arg1,
            self._arg_inner_access[0],
            self._size_frame,
            self._size_inner,
        )
        return interpret(self, new_frame, self._maximum_number_of_stack_elements)

    def invoke_3(self, rcvr, arg1, arg2):
        new_frame = create_frame_3(
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
            rcvr,
            arg1,
            arg2,
        )
        return interpret(self, new_frame, self._maximum_number_of_stack_elements)

    def invoke_n(self, stack, stack_ptr):
        new_frame = create_frame(
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
            stack,
            stack_ptr,
            self._number_of_arguments,
        )

        result = interpret(self, new_frame, self._maximum_number_of_stack_elements)
        return stack_pop_old_arguments_and_push_result(
            stack, stack_ptr, self._number_of_arguments, result
        )


class BcMethodNLR(BcMethod):
    def invoke_1(self, rcvr):
        new_frame = create_frame_1(rcvr, self._size_frame, self._size_inner)
        return _interp_with_nlr(self, new_frame, self._maximum_number_of_stack_elements)

    def invoke_2(self, rcvr, arg1):
        new_frame = create_frame_2(
            rcvr,
            arg1,
            self._arg_inner_access[0],
            self._size_frame,
            self._size_inner,
        )
        return _interp_with_nlr(self, new_frame, self._maximum_number_of_stack_elements)

    def invoke_3(self, rcvr, arg1, arg2):
        new_frame = create_frame_3(
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
            rcvr,
            arg1,
            arg2,
        )
        return _interp_with_nlr(self, new_frame, self._maximum_number_of_stack_elements)

    def invoke_n(self, stack, stack_ptr):
        new_frame = create_frame(
            self._arg_inner_access,
            self._size_frame,
            self._size_inner,
            stack,
            stack_ptr,
            self._number_of_arguments,
        )
        inner = get_inner_as_context(new_frame)

        try:
            result = interpret(self, new_frame, self._maximum_number_of_stack_elements)
            stack_ptr = stack_pop_old_arguments_and_push_result(
                stack, stack_ptr, self._number_of_arguments, result
            )
            mark_as_no_longer_on_stack(inner)
            return stack_ptr
        except ReturnException as e:
            mark_as_no_longer_on_stack(inner)
            if e.has_reached_target(inner):
                return stack_pop_old_arguments_and_push_result(
                    stack, stack_ptr, self._number_of_arguments, e.get_result()
                )
            raise e
