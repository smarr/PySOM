from rtruffle.node import Node


class ExpressionNode(Node):
    def __init__(self, source_section):
        Node.__init__(self, source_section)

    def create_trivial_method(self, _signature):
        return None

    def is_trivial_in_sequence(self):
        return False

    def handle_inlining(self, mgenc):  # pylint: disable=W
        pass

    def handle_outer_inlined(
        self, removed_ctx_level, mgenc_with_inlined
    ):  # pylint: disable=W
        pass
