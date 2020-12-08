import unittest
from rtruffle.node import Node


class NodeTest(unittest.TestCase):

    def test_adopt_child(self):
        child = ChildNode()
        parent = RootNode()

        self.assertIsNone(child.get_parent())
        parent.adopt_child(child)

        self.assertIs(parent, child.get_parent())

    def test_adopt_children(self):
        children = [ChildNode() for _ in range(0, 10)]
        parent = RootNode()

        self.assertIsNot(children[0], children[1])
        for child in children:
            self.assertIsNone(child.get_parent())

        parent.adopt_children(children)
        for child in children:
            self.assertIs(parent, child.get_parent())

    def test_replace_1(self):
        child1 = ChildNode()
        parent = RootNode(child1, None)

        self.assertIs(child1, parent._child_node1)
        self.assertIsNone(parent._child_node2)

        child2 = ChildNode()
        child1.replace(child2)

        self.assertIs(child2, parent._child_node1)
        self.assertIsNone(parent._child_node2)

    def test_replace_2(self):
        child1 = ChildNode()
        parent = RootNode(None, child1)

        self.assertIsNone(parent._child_node1)
        self.assertIs(child1, parent._child_node2)

        child2 = ChildNode()
        child1.replace(child2)

        self.assertIsNone(parent._child_node1)
        self.assertIs(child2, parent._child_node2)

    def test_replace_in_children(self):
        child1 = ChildNode()
        child2 = ChildNode()
        parent = RootNodeWithChildList([child1, child1, child1])

        for each in parent._child_nodes:
            self.assertIs(each, child1)

        child1.replace(child2)

        for each in parent._child_nodes:
            self.assertIs(each, child2)


class RootNode(Node):

    _child_nodes_ = ['_child_node1', '_child_node2']

    def __init__(self, child_node1 = None, child_node2 = None):
        Node.__init__(self)
        self._child_node1 = self.adopt_child(child_node1)
        self._child_node2 = self.adopt_child(child_node2)


class RootNodeWithChildList(Node):

    _child_nodes_ = ['_child_nodes[*]']

    def __init__(self, child_nodes = None):
        Node.__init__(self)
        assert isinstance(child_nodes, list)
        self._child_nodes = self.adopt_children(child_nodes)


class ChildNode(Node):
    pass
