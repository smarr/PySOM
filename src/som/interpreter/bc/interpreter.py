from som.interpreter.bc.bytecodes import bytecode_length, Bytecodes
from som.interpreter.control_flow import ReturnException
from som.vmobjects.array import Array
from som.vmobjects.block_bc import BcBlock

from rlib import jit


class Interpreter(object):

    _immutable_fields_ = ["universe"]

    def __init__(self, universe):
        self.universe   = universe

    def _do_push_global(self, bytecode_index, frame, method):
        # Handle the push global bytecode
        global_name = method.get_constant(bytecode_index)

        # Get the global from the universe
        glob = self.universe.get_global(global_name)

        if glob:
            # Push the global onto the stack
            frame.push(glob)
        else:
            # Send 'unknownGlobal:' to self
            self._send_unknown_global(self.get_self_dynamically(frame), frame, global_name)

    def _do_pop_field(self, bytecode_index, frame, method):
        # Handle the pop field bytecode
        field_index = method.get_bytecode(bytecode_index + 1)
        ctx_level = method.get_bytecode(bytecode_index + 2)

        # Set the field with the computed index to the value popped from the stack
        self.get_self(frame, ctx_level).set_field(field_index, frame.pop())

    def _do_super_send(self, bytecode_index, frame, method):
        signature = method.get_constant(bytecode_index)

        receiver_class = method.get_holder().get_super_class()
        invokable = receiver_class.lookup_invokable(signature)
        method.set_inline_cache(bytecode_index, receiver_class, invokable)
        method.set_bytecode(bytecode_index, Bytecodes.q_super_send)

        if invokable:
            invokable.invoke(frame, self)
        else:
            num_args = invokable.get_number_of_signature_arguments()
            receiver = frame.get_stack_element(num_args - 1)
            self._send_does_not_understand(receiver, frame, invokable.get_signature())

    def _do_q_super_send(self, bytecode_index, frame, method):
        invokable = method.get_inline_cache_invokable(bytecode_index)
        if invokable:
            invokable.invoke(frame, self)
        else:
            num_args = invokable.get_number_of_signature_arguments()
            receiver = frame.get_stack_element(num_args - 1)
            self._send_does_not_understand(receiver, frame, invokable.get_signature())

    @jit.unroll_safe
    def _do_return_non_local(self, frame, ctx_level):
        # get result from stack
        result = frame.top()

        # Compute the context for the non-local return
        context = frame.get_context_at(ctx_level)

        # Make sure the block context is still on the stack
        if not context.has_previous_frame():
            # Try to recover by sending 'escapedBlock:' to the sending object
            # this can get a bit nasty when using nested blocks. In this case
            # the "sender" will be the surrounding block and not the object
            # that actually sent the 'value' message.
            block  = frame.get_argument(0, 0)
            sender = frame.get_previous_frame().get_outer_context().get_argument(0, 0)

            # ... and execute the escapedBlock message instead
            self._send_escaped_block(sender, frame, block)
            return frame.top()

        raise ReturnException(result, context)

    def _do_send(self, bytecode_index, frame, method):
        # Handle the send bytecode
        signature = method.get_constant(bytecode_index)

        # Get the number of arguments from the signature
        num_args = signature.get_number_of_signature_arguments()

        # Get the receiver from the stack
        receiver = frame.get_stack_element(num_args - 1)

        # Send the message
        self._send(method, frame, signature, receiver.get_class(self.universe),
                   bytecode_index)

    @jit.unroll_safe
    def interpret(self, method, frame):
        current_bc_idx = 0
        while True:
            # since methods cannot contain loops (all loops are done via primitives)
            # profiling only needs to be done on pc = 0
            if current_bc_idx == 0:
                jitdriver.can_enter_jit(
                    bytecode_index=current_bc_idx, interp=self, method=method, frame=frame)
            jitdriver.jit_merge_point(
                bytecode_index=current_bc_idx, interp=self, method=method, frame=frame)

            bytecode = method.get_bytecode(current_bc_idx)

            # Get the length of the current bytecode
            bc_length = bytecode_length(bytecode)

            # Compute the next bytecode index
            next_bc_idx = current_bc_idx + bc_length

            # Handle the current bytecode
            if   bytecode == Bytecodes.halt:                            # BC: 0
                return frame.top()
            elif bytecode == Bytecodes.dup:                             # BC: 1
                frame.push(frame.top())
            elif bytecode == Bytecodes.push_local:                      # BC: 2
                frame.push(
                    frame.get_local(
                        method.get_bytecode(current_bc_idx + 1),
                        method.get_bytecode(current_bc_idx + 2)))
            elif bytecode == Bytecodes.push_argument:                   # BC: 3
                frame.push(
                    frame.get_argument(
                        method.get_bytecode(current_bc_idx + 1),
                        method.get_bytecode(current_bc_idx + 2)))
            elif bytecode == Bytecodes.push_field:                      # BC: 4
                field_index = method.get_bytecode(current_bc_idx + 1)
                ctx_level = method.get_bytecode(current_bc_idx + 2)
                frame.push(self.get_self(frame, ctx_level).get_field(field_index))
            elif bytecode == Bytecodes.push_block:                      # BC: 5
                block_method = method.get_constant(current_bc_idx)
                frame.push(BcBlock(block_method, frame))
            elif bytecode == Bytecodes.push_constant:                   # BC: 6
                frame.push(method.get_constant(current_bc_idx))
            elif bytecode == Bytecodes.push_global:                     # BC: 7
                self._do_push_global(current_bc_idx, frame, method)
            elif bytecode == Bytecodes.pop:                             # BC: 8
                frame.pop()
            elif bytecode == Bytecodes.pop_local:                       # BC: 9
                frame.set_local(
                    method.get_bytecode(current_bc_idx + 1),
                    method.get_bytecode(current_bc_idx + 2),
                    frame.pop())
            elif bytecode == Bytecodes.pop_argument:                    # BC:10
                frame.set_argument(
                    method.get_bytecode(current_bc_idx + 1),
                    method.get_bytecode(current_bc_idx + 2),
                    frame.pop())
            elif bytecode == Bytecodes.pop_field:                       # BC:11
                self._do_pop_field(current_bc_idx, frame, method)
            elif bytecode == Bytecodes.send:                            # BC:12
                self._do_send(current_bc_idx, frame, method)
            elif bytecode == Bytecodes.super_send:                      # BC:13
                self._do_super_send(current_bc_idx, frame, method)
            elif bytecode == Bytecodes.return_local:                    # BC:14
                return frame.top()
            elif bytecode == Bytecodes.return_non_local:                # BC:15
                return self._do_return_non_local(frame, method.get_bytecode(current_bc_idx + 1))
            elif bytecode == Bytecodes.return_self:
                return frame.get_argument(0, 0)
            elif bytecode == Bytecodes.inc:
                val = frame.top()
                from som.vmobjects.integer import Integer
                from som.vmobjects.double import Double
                from som.vmobjects.biginteger import BigInteger
                if isinstance(val, Integer):
                    result = val.prim_inc()
                elif isinstance(val, Double):
                    result = val.prim_inc()
                elif isinstance(val, BigInteger):
                    result = val.prim_inc()
                else:
                    return self._not_yet_implemented()
                frame.set_top(result)
            elif bytecode == Bytecodes.dec:
                val = frame.top()
                from som.vmobjects.integer import Integer
                from som.vmobjects.double import Double
                from som.vmobjects.biginteger import BigInteger
                if isinstance(val, Integer):
                    result = val.prim_dec()
                elif isinstance(val, Double):
                    result = val.prim_dec()
                elif isinstance(val, BigInteger):
                    result = val.prim_dec()
                else:
                    return self._not_yet_implemented()
                frame.set_top(result)
            elif bytecode == Bytecodes.q_super_send:
                self._do_q_super_send(current_bc_idx, frame, method)
            else:
                self._unknown_bytecode(bytecode)

            current_bc_idx = next_bc_idx

    def _not_yet_implemented(self):
        raise Exception("Not yet implemented")

    def _unknown_bytecode(self, bytecode):
        raise Exception("Unknown bytecode: " + str(bytecode))

    @staticmethod
    def get_self(frame, ctx_level):
        # Get the self object from the interpreter
        return frame.get_argument(0, ctx_level)

    @staticmethod
    def get_self_dynamically(frame):
        # Get the self object from the interpreter
        return frame.get_outer_context().get_argument(0, 0)

    def _send(self, m, frame, selector, receiver_class, bytecode_index):
        # selector.inc_send_count()

        # First try the inline cache
        cached_class = m.get_inline_cache_class(bytecode_index)
        if cached_class == receiver_class:
            invokable = m.get_inline_cache_invokable(bytecode_index)
        else:
            if not cached_class:
                # Lookup the invokable with the given signature
                invokable = receiver_class.lookup_invokable(selector)
                m.set_inline_cache(bytecode_index, receiver_class, invokable)
            else:
                # the bytecode index after the send is used by the selector constant,
                # and can be used safely as another cache item
                cached_class = m.get_inline_cache_class(bytecode_index + 1)
                if cached_class == receiver_class:
                    invokable = m.get_inline_cache_invokable(bytecode_index + 1)
                else:
                    invokable = receiver_class.lookup_invokable(selector)
                    if not cached_class:
                        m.set_inline_cache(bytecode_index + 1, receiver_class, invokable)

        if invokable:
            invokable.invoke(frame, self)
        else:
            num_args = selector.get_number_of_signature_arguments()

            # Compute the receiver
            receiver = frame.get_stack_element(num_args - 1)
            self._send_does_not_understand(receiver, frame, selector)

    def _send_does_not_understand(self, receiver, frame, selector):
        # ignore self
        number_of_arguments = selector.get_number_of_signature_arguments() - 1
        arguments_array = Array.from_size(number_of_arguments)

        # Remove all arguments and put them in the freshly allocated array
        i = number_of_arguments - 1
        while i >= 0:
            arguments_array.set_indexable_field(i, frame.pop())
            i -= 1

        frame.pop()  # pop self from stack
        args = [selector, arguments_array]
        self._lookup_and_send(receiver, frame, "doesNotUnderstand:arguments:", args)

    def _send_unknown_global(self, receiver, frame, global_name):
        arguments = [global_name]
        self._lookup_and_send(receiver, frame, "unknownGlobal:", arguments)

    def _send_escaped_block(self, receiver, frame, block):
        arguments = [block]
        self._lookup_and_send(receiver, frame, "escapedBlock:", arguments)

    def _lookup_and_send(self, receiver, frame, selector_string, arguments):
        selector = self.universe.symbol_for(selector_string)
        invokable = receiver.get_class(self.universe).lookup_invokable(selector)

        frame.push(receiver)
        for arg in arguments:
            frame.push(arg)

        invokable.invoke(frame, self)


def get_printable_location(bytecode_index, interp, method):
    from som.vmobjects.method_bc import BcMethod
    from som.interpreter.bc.bytecodes import bytecode_as_str
    assert isinstance(method, BcMethod)
    bc = method.get_bytecode(bytecode_index)
    return "%s @ %d in %s" % (bytecode_as_str(bc),
                              bytecode_index,
                              method.merge_point_string())


jitdriver = jit.JitDriver(
    name='Interpreter',
    greens=['bytecode_index', 'interp', 'method'],
    reds=['frame'],
    # virtualizables=['frame'],
    get_printable_location=get_printable_location,
    # the next line is a workaround around a likely bug in RPython
    # for some reason, the inlining heuristics default to "never inline" when
    # two different jit drivers are involved (in our case, the primitive
    # driver, and this one).

    # the next line says that calls involving this jitdriver should always be
    # inlined once (which means that things like Integer>>< will be inlined
    # into a while loop again, when enabling this drivers).
    should_unroll_one_iteration = lambda bytecode_index, inter, method: True)


def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()
