from rtruffle.node import Node


class ExpressionNode(Node):

    def __init__(self, source_section):
        Node.__init__(self, source_section)

    def is_super_node(self):
        return False
