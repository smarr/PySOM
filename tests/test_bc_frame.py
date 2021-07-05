import unittest

from som.interpreter.ast.frame import FRAME_AND_INNER_RCVR_IDX, read_frame, read_inner
from som.interpreter.bc.frame import (
    create_frame,
    stack_top,
    create_bootstrap_frame,
    stack_push,
    stack_pop,
)
from som.vm.globals import trueObject, falseObject
from som.vmobjects.integer import Integer

_MIN_FRAME_SIZE = 1 + 1 + 1  # Inner, Receiver, StackPtr


class FrameTest(unittest.TestCase):
    def test_create_empty_frame(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        frame = create_frame([], _MIN_FRAME_SIZE, 0, 1, bootstrap_frame, 1)

        self.assertIs(
            trueObject, stack_top(frame), "top should be pointing at the receiver"
        )

    def test_frame_with_4_stack_elements(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        frame = create_frame([], _MIN_FRAME_SIZE + 4, 0, 1, bootstrap_frame, 1)

        self.assertIs(
            trueObject, stack_top(frame), "top should be pointing at the receiver"
        )

        stack_push(frame, falseObject)
        stack_push(frame, falseObject)
        stack_push(frame, falseObject)
        stack_push(frame, falseObject)

        self.assertIs(falseObject, stack_pop(frame))
        self.assertIs(falseObject, stack_pop(frame))
        self.assertIs(falseObject, stack_pop(frame))
        self.assertIs(falseObject, stack_pop(frame))

        self.assertIs(
            trueObject, stack_top(frame), "top should be pointing at the receiver"
        )

    def test_call_argument_handling_all_frame(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        num_args = 4
        frame = create_frame([], _MIN_FRAME_SIZE + num_args, 0, 1, bootstrap_frame, 1)

        for i in range(num_args):
            stack_push(frame, Integer(i))

        callee_frame = create_frame(
            [False] * (num_args - 1), _MIN_FRAME_SIZE + num_args, 0, 0, frame, num_args
        )

        for i in range(num_args):
            self.assertEqual(
                i,
                read_frame(
                    callee_frame, FRAME_AND_INNER_RCVR_IDX + i
                ).get_embedded_integer(),
            )

    def test_call_argument_handling_mix_frame_and_inner(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        num_args = 6
        frame = create_frame([], _MIN_FRAME_SIZE + num_args, 0, 1, bootstrap_frame, 1)

        for i in range(num_args):
            stack_push(frame, Integer(i))

        arg_access_inner = [True, False, True, False, True]
        arg_access_inner.reverse()
        callee_frame = create_frame(
            arg_access_inner, _MIN_FRAME_SIZE + num_args, 2 + 3, 0, frame, num_args
        )

        self.assertEqual(
            0, read_frame(callee_frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )
        self.assertEqual(
            1,
            read_inner(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 1
            ).get_embedded_integer(),
        )
        self.assertEqual(
            2,
            read_frame(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 1
            ).get_embedded_integer(),
        )
        self.assertEqual(
            3,
            read_inner(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 2
            ).get_embedded_integer(),
        )
        self.assertEqual(
            4,
            read_frame(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 2
            ).get_embedded_integer(),
        )
        self.assertEqual(
            5,
            read_inner(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 3
            ).get_embedded_integer(),
        )

    def test_call_argument_handling_first_frame_then_inner(self):
        bootstrap_frame = create_bootstrap_frame(trueObject)
        num_args = 6
        frame = create_frame([], _MIN_FRAME_SIZE + num_args, 0, 1, bootstrap_frame, 1)

        for i in range(num_args):
            stack_push(frame, Integer(i))

        arg_access_inner = [False, False, False, True, True]
        arg_access_inner.reverse()
        callee_frame = create_frame(
            arg_access_inner, _MIN_FRAME_SIZE + num_args, 2 + 3, 0, frame, num_args
        )

        self.assertEqual(
            0, read_frame(callee_frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )
        self.assertEqual(
            1,
            read_frame(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 1
            ).get_embedded_integer(),
        )
        self.assertEqual(
            2,
            read_frame(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 2
            ).get_embedded_integer(),
        )
        self.assertEqual(
            3,
            read_frame(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 3
            ).get_embedded_integer(),
        )
        self.assertEqual(
            4,
            read_inner(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 1
            ).get_embedded_integer(),
        )
        self.assertEqual(
            5,
            read_inner(
                callee_frame, FRAME_AND_INNER_RCVR_IDX + 2
            ).get_embedded_integer(),
        )
