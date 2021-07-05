import unittest

from som.interpreter.bc.frame import create_frame, stack_top, create_bootstrap_frame, stack_push, \
    stack_pop
from som.vm.globals import trueObject, falseObject

_MIN_FRAME_SIZE = 1 + 1 + 1  # Inner, Receiver, StackPtr


class FrameTest(unittest.TestCase):

    def test_create_empty_frame(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        frame = create_frame([], _MIN_FRAME_SIZE, 0, 1, bootstrap_frame, 1)

        self.assertIs(trueObject, stack_top(frame), "top should be pointing at the receiver")

    def test_frame_with_4_stack_elements(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        frame = create_frame([], _MIN_FRAME_SIZE + 4, 0, 1, bootstrap_frame, 1)

        self.assertIs(trueObject, stack_top(frame), "top should be pointing at the receiver")

        stack_push(frame, falseObject)
        stack_push(frame, falseObject)
        stack_push(frame, falseObject)
        stack_push(frame, falseObject)

        self.assertIs(falseObject, stack_pop(frame))
        self.assertIs(falseObject, stack_pop(frame))
        self.assertIs(falseObject, stack_pop(frame))
        self.assertIs(falseObject, stack_pop(frame))

        self.assertIs(trueObject, stack_top(frame), "top should be pointing at the receiver")
