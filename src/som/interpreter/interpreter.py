from som.interpreter.bytecodes import Bytecodes

class Interpreter(object):
    
    def __init__(self, universe):
        self._universe = universe
        self._frame    = None
        self._dispatch_table = [self._do_halt,
                                self._do_dup,
                                self._do_push_local,
                                self._do_push_argument,
                                self._do_push_field,
                                self._do_push_block,
                                self._do_push_constant,
                                self._do_push_global,
                                self._do_pop,
                                self._do_pop_local,
                                self._do_pop_argument,
                                self._do_pop_field,
                                self._do_send,
                                self._do_super_send,
                                self._do_return_local,
                                self._do_return_non_local]
    
    def get_universe(self):
        return self._universe

    class InterpreterHalt(Exception):
        pass
    
    def _do_halt(self, bytecode_index):
        raise self.InterpreterHalt()
    
    def _do_dup(self, bytecode_index):
        # Handle the dup bytecode
        self.get_frame().push(self.get_frame().get_stack_element(0))

    def _do_push_local(self, bytecode_index):
        # Handle the push local bytecode
        self.get_frame().push(
            self.get_frame().get_local(self.get_method().get_bytecode(bytecode_index + 1),
            self.get_method().get_bytecode(bytecode_index + 2)))

    def _do_push_argument(self, bytecode_index):
        # Handle the push argument bytecode
        self.get_frame().push(
            self.get_frame().get_argument(self.get_method().get_bytecode(bytecode_index + 1),
            self.get_method().get_bytecode(bytecode_index + 2)))

    def _do_push_field(self, bytecode_index):
        # Handle the push field bytecode
        field_index = self.get_method().get_bytecode(bytecode_index + 1)

        # Push the field with the computed index onto the stack
        self.get_frame().push(self.get_self().get_field(field_index))

    def _do_push_block(self, bytecode_index):
        # Handle the push block bytecode
        block_method = self.get_method().get_constant(bytecode_index)

        # Push a new block with the current self.get_frame() as context onto the
        # stack
        self.get_frame().push(
            self._universe.new_block(block_method, self.get_frame(),
            block_method.get_number_of_arguments()))

    def _do_push_constant(self, bytecode_index):
        # Handle the push constant bytecode
        self.get_frame().push(self.get_method().get_constant(bytecode_index))

    def _do_push_global(self, bytecode_index):
        # Handle the push global bytecode
        global_name = self.get_method().get_constant(bytecode_index)

        # Get the global from the universe
        glob = self._universe.get_global(global_name)

        if glob:
            # Push the global onto the stack
            self.get_frame().push(glob)
        else:
            # Send 'unknownGlobal:' to self
            self.get_self().send_unknown_global(global_name, self._universe, self)

    def _do_pop(self, bytecode_index):
        # Handle the pop bytecode
        self.get_frame().pop()

    def _do_pop_local(self, bytecode_index):
        # Handle the pop local bytecode
        self.get_frame().set_local(self.get_method().get_bytecode(bytecode_index + 1),
                                   self.get_method().get_bytecode(bytecode_index + 2),
                                   self.get_frame().pop())

    def _do_pop_argument(self, bytecode_index):
        # Handle the pop argument bytecode
        self.get_frame().set_argument(self.get_method().get_bytecode(bytecode_index + 1),
                                      self.get_method().get_bytecode(bytecode_index + 2),
                                      self.get_frame().pop())

    def _do_pop_field(self, bytecode_index):
        # Handle the pop field bytecode
        field_index = self.get_method().get_bytecode(bytecode_index + 1)

        # Set the field with the computed index to the value popped from the stack
        self.get_self().set_field(field_index, self.get_frame().pop())

    def _do_super_send(self, bytecode_index):
        # Handle the super send bytecode
        signature = self.get_method().get_constant(bytecode_index)

        # Send the message
        # Lookup the invokable with the given signature
        invokable = self.get_method().get_holder().get_super_class().lookup_invokable(signature)

        if invokable:
            # Invoke the invokable in the current frame
            invokable.invoke(self.get_frame(), self)
        else:
            # Compute the number of arguments
            num_args = signature.get_number_of_signature_arguments()

            # Compute the receiver
            receiver = self.get_frame().get_stack_element(num_args - 1)

            receiver.send_does_not_understand(signature, self._universe, self)

    def _do_return_local(self, bytecode_index):
        # Handle the return local bytecode
        result = self.get_frame().pop()

        # Pop the top frame and push the result
        self._pop_frame_and_push_result(result)

    def _do_return_non_local(self, bytecode_index):
        # Handle the return non local bytecode
        result = self.get_frame().pop()

        # Compute the context for the non-local return
        context = self.get_frame().get_outer_context(self._universe.nilObject)

        # Make sure the block context is still on the stack
        if not context.has_previous_frame(self._universe.nilObject):
            # Try to recover by sending 'escapedBlock:' to the sending object
            # this can get a bit nasty when using nested blocks. In this case
            # the "sender" will be the surrounding block and not the object
            # that actually sent the 'value' message.
            block  = self.get_frame().get_argument(0, 0)
            sender = self.get_frame().get_previous_frame().get_outer_context(self._universe.nilObject).get_argument(0, 0)

            # pop the frame of the currently executing block...
            self._pop_frame()

            # ... and execute the escapedBlock message instead
            sender.send_escaped_block(block, self._universe, self)
            return

        # Unwind the frames
        while self.get_frame() != context:
            self._pop_frame()

        # Pop the top frame and push the result
        self._pop_frame_and_push_result(result)

    def _do_send(self, bytecode_index):
        # Handle the send bytecode
        signature = self.get_method().get_constant(bytecode_index)

        # Get the number of arguments from the signature
        num_args = signature.get_number_of_signature_arguments()

        # Get the receiver from the stack
        receiver = self.get_frame().get_stack_element(num_args - 1)

        # Send the message
        self._send(signature, receiver.get_class(), bytecode_index)


    def start(self):
        try:
            # Iterate through the bytecodes
            while True:
                # Get the current bytecode index
                bytecode_index = self.get_frame().get_bytecode_index()
                
                # Get the current bytecode
                bytecode = self.get_method().get_bytecode(bytecode_index)
    
                # Get the length of the current bytecode
                bytecode_length = Bytecodes.get_bytecode_length(bytecode)
    
                # Compute the next bytecode index
                next_bytecode_index = bytecode_index + bytecode_length
    
                # Update the bytecode index of the frame
                self.get_frame().set_bytecode_index(next_bytecode_index)
    
                # Handle the current bytecode
                self._dispatch_table[bytecode](bytecode_index)
        
        except self.InterpreterHalt:
            return self.get_frame().get_stack_element(0)
            
    def push_new_frame(self, method, context):
        # Allocate a new frame and make it the current one
        self._frame = self._universe.new_frame(self._frame, method, context)

        # Return the freshly allocated and pushed frame
        return self._frame


    def get_frame(self):
        # Get the frame from the interpreter
        return self._frame

    def get_method(self):
        # Get the method from the interpreter
        return self.get_frame().get_method()

    def get_self(self):
        # Get the self object from the interpreter
        return self.get_frame().get_outer_context(self._universe.nilObject).get_argument(0, 0)

    def _send(self, selector, receiver_class, bytecode_index):
        # First try the inline cache
        m = self.get_method()
        cached_class = m.get_inline_cache_class(bytecode_index)
        if cached_class == receiver_class:
            invokable = m.get_inline_cache_invokable(bytecode_index)
        else:
            if not cached_class:
                # Lookup the invokable with the given signature
                invokable = receiver_class.lookup_invokable(selector)
                m.set_inline_cache(bytecode_index, receiver_class, invokable)
            else:
                cached_class = m.get_inline_cache_class(bytecode_index + 1) # the bytecode index after the send is used by the selector constant, and can be used safely as another cache item
                if cached_class == receiver_class:
                    invokable = m.get_inline_cache_invokable(bytecode_index + 1)
                else:
                    invokable = receiver_class.lookup_invokable(selector)
                    if not cached_class:
                        m.set_inline_cache(bytecode_index + 1, receiver_class, invokable)
        
        if invokable:
            # Invoke the invokable in the current frame
            invokable.invoke(self.get_frame(), self)
        else:
            num_args = selector.get_number_of_signature_arguments()

            # Compute the receiver
            receiver = self._frame.get_stack_element(num_args - 1)
            receiver.send_does_not_understand(selector, self._universe, self)

    def _pop_frame(self):
        # Save a reference to the top frame
        result = self._frame

        # Pop the top frame from the frame stack
        self._frame = self._frame.get_previous_frame()

        # Destroy the previous pointer on the old top frame
        result.clear_previous_frame(self._universe.nilObject)

        # Return the popped frame
        return result

    def _pop_frame_and_push_result(self, result):
        # Pop the top frame from the interpreter frame stack and compute the
        # number of arguments
        num_args = self._pop_frame().get_method().get_number_of_arguments()

        # Pop the arguments
        for _ in range(0, num_args):
            self.get_frame().pop()

        # Push the result
        self.get_frame().push(result)
