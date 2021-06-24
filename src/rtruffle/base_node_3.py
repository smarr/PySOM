from rtruffle.abstract_node import AbstractNode, NodeInitializeMetaClass


class BaseNode(AbstractNode, metaclass=NodeInitializeMetaClass):
    _immutable_fields_ = ["source_section", "parent"]
    _child_nodes_ = []
