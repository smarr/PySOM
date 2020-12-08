from rtruffle.abstract_node import AbstractNode, NodeInitializeMetaClass


class BaseNode(AbstractNode, metaclass=NodeInitializeMetaClass):
    _immutable_fields_ = ['_source_section', '_parent']
    _child_nodes_ = []
