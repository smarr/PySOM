from rlib.unroll import unrolling_iterable


class AbstractNode(object):
    pass


def _get_all_child_fields(cls):
    field_names = []
    while cls is not AbstractNode:
        if hasattr(cls, '_child_nodes_'):
            field_names = field_names + cls._child_nodes_
        cls = cls.__base__
    return field_names


def _generate_replace_method(cls):
    child_fields = unrolling_iterable(_get_all_child_fields(cls))

    def _replace_child_with(parent_node, old_child, new_child):
        was_replaced = False
        for child_slot in child_fields:
            if child_slot.endswith('[*]'):
                slot_name = child_slot[:-3]
                nodes = getattr(parent_node, slot_name)
                if nodes and old_child in nodes:
                    # update old list, because iterators might have a copy of it
                    for i, n in enumerate(nodes):
                        if n is old_child:
                            nodes[i] = new_child
                    setattr(parent_node, slot_name, nodes[:])  # TODO: figure out whether we need the copy of the list here
                    was_replaced = True
            else:
                current = getattr(parent_node, child_slot)
                if current is old_child:
                    setattr(parent_node, child_slot, new_child)
                    was_replaced = True
        # TODO: method recursion is a problem causing specialization more than
        #       once of a node if the containing method is already on the stack
        # if not was_replaced:
        #     raise ValueError("%s was not a direct child node of %s" % (
        #         old_child, parent_node))
        return new_child

    cls._replace_child_with = _replace_child_with


class NodeInitializeMetaClass(type):
    def __init__(cls, name, bases, dic):
        type.__init__(cls, name, bases, dic)
        cls._initialize_node_class()

    def _initialize_node_class(cls):
        _generate_replace_method(cls)
