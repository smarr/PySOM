import unittest

from som.interpreter.ast.frame import (
    FRAME_AND_INNER_RCVR_IDX,
    read_frame,
    read_inner,
    create_frame_1,
    create_frame_2,
)
from som.interpreter.bc.frame import (
    create_frame,
)
from som.vmobjects.integer import Integer

_MIN_FRAME_SIZE = 1 + 1  # Inner, Receiver


class FrameTest(unittest.TestCase):
    def test_call_argument_handling_all_frame(self):
        num_args = 4
        prev_stack = [Integer(i) for i in range(num_args)]

        callee_frame = create_frame(
            [False] * (num_args - 1),
            _MIN_FRAME_SIZE + num_args,
            0,
            prev_stack,
            num_args - 1,
            num_args,
        )

        for i in range(num_args):
            self.assertEqual(
                i,
                read_frame(
                    callee_frame, FRAME_AND_INNER_RCVR_IDX + i
                ).get_embedded_integer(),
            )

    def test_call_argument_handling_mix_frame_and_inner(self):
        num_args = 6
        prev_stack = [Integer(i) for i in range(num_args)]

        arg_access_inner = [True, False, True, False, True]
        arg_access_inner.reverse()
        callee_frame = create_frame(
            arg_access_inner,
            _MIN_FRAME_SIZE + num_args,
            2 + 3,
            prev_stack,
            num_args - 1,
            num_args,
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
        num_args = 6

        prev_stack = [Integer(i) for i in range(num_args)]

        arg_access_inner = [False, False, False, True, True]
        arg_access_inner.reverse()
        callee_frame = create_frame(
            arg_access_inner,
            _MIN_FRAME_SIZE + num_args,
            2 + 3,
            prev_stack,
            num_args - 1,
            num_args,
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

    def test_create_frame_1(self):
        rcvr = Integer(1)
        frame = create_frame_1(rcvr, _MIN_FRAME_SIZE, _MIN_FRAME_SIZE)

        self.assertEqual(
            1, read_inner(frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )
        self.assertEqual(
            1, read_frame(frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )

    def test_create_frame_2_inner(self):
        rcvr = Integer(1)
        arg = Integer(2)
        frame = create_frame_2(rcvr, arg, True, _MIN_FRAME_SIZE, _MIN_FRAME_SIZE + 1)

        self.assertEqual(
            1, read_inner(frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )
        self.assertEqual(
            1, read_frame(frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )

        self.assertEqual(
            2, read_inner(frame, FRAME_AND_INNER_RCVR_IDX + 1).get_embedded_integer()
        )

    def test_create_frame_2_frame(self):
        rcvr = Integer(1)
        arg = Integer(2)
        frame = create_frame_2(rcvr, arg, False, _MIN_FRAME_SIZE + 1, _MIN_FRAME_SIZE)

        self.assertEqual(
            1, read_inner(frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )
        self.assertEqual(
            1, read_frame(frame, FRAME_AND_INNER_RCVR_IDX).get_embedded_integer()
        )

        self.assertEqual(
            2, read_frame(frame, FRAME_AND_INNER_RCVR_IDX + 1).get_embedded_integer()
        )
