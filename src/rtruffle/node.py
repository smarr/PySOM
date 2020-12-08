from rtruffle.source_section import SourceSection

import sys

if sys.version_info.major > 2:
    from rtruffle.base_node_3 import BaseNode
else:
    from rtruffle.base_node_2 import BaseNode


class Node(BaseNode):

    def __init__(self, source_section = None):
        assert (source_section is None or
                isinstance(source_section, SourceSection))
        self._source_section = source_section
        self._parent         = None

    def get_parent(self):
        return self._parent

    def assign_source_section(self, source_section):
        assert isinstance(source_section, SourceSection)
        if self._source_section:
            raise ValueError("Source section already set.")
        self._source_section = source_section

    def get_source_section(self):
        return self._source_section

    def adopt_child(self, node):
        assert isinstance(node, Node) or node is None
        if node:
            node._parent = self
        return node

    def adopt_children(self, nodes):
        if nodes is None:
            return None

        children = nodes[:]  # we return here a copy to make it clear to RPython
                             # that the list is not resized, and,
                             # the quasi-immutable support does not work on
                             # element-level, so, we will need to copy the lists
                             # when replacing child nodes

        for child in children:
            child._parent = self
        return children

    def replace(self, node):
        if node:
            self._parent._replace_child_with(self, node)
            node._parent = self._parent
            return node
        else:
            return None

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._source_section)
