from rtruffle.abstract_node import AbstractNode, NodeInitializeMetaClass


class BaseNode(AbstractNode):
    __metaclass__ = NodeInitializeMetaClass

    _immutable_fields_ = ["source_section", "parent"]
    _child_nodes_ = []
