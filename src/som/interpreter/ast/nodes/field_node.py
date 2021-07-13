from rlib.jit import elidable_promote
from som.interpreter.objectstorage.layout_transitions import (
    UninitializedStorageLocationException,
    GeneralizeStorageLocationException,
)
from som.interpreter.objectstorage.storage_location import create_generic_access_node
from som.vmobjects.abstract_object import AbstractObject
from som.vmobjects.object_with_layout import ObjectWithLayout

from som.interpreter.ast.nodes.expression_node import ExpressionNode


_MAX_CHAIN_LENGTH = 6


class _AbstractFieldNode(ExpressionNode):
    _immutable_fields_ = ["_self_exp?", "_field_idx", "_access_node?"]
    _child_nodes_ = ["_self_exp"]

    def __init__(self, self_exp, field_idx, source_section):
        ExpressionNode.__init__(self, source_section)
        self._self_exp = self.adopt_child(self_exp)
        self._field_idx = field_idx
        self._access_node = None

    @elidable_promote("0,1")
    def _lookup(self, layout, obj):
        first = self._access_node
        cache = first
        while cache is not None:
            if cache.layout is layout:
                return cache
            cache = cache.next_entry

        if not layout.is_latest:
            obj.update_layout_to_match_class()
            return self._lookup(obj.get_object_layout(), obj)

        # this is the generic dispatch node
        if first and first.layout is None:
            return first

        return self._specialize(layout)

    def _get_cache_size_and_drop_old_entries(self):
        size = 0
        prev = None
        cache = self._access_node
        while cache is not None:
            if not cache.layout.is_latest:
                # drop from cache if not latest
                if prev is None:
                    self._access_node = cache.next_entry
                else:
                    prev.next_entry = cache.next_entry
            else:
                size += 1
                prev = cache

            cache = cache.next_entry
        return size

    def _specialize(self, layout):
        cache_size = self._get_cache_size_and_drop_old_entries()

        if cache_size < _MAX_CHAIN_LENGTH:
            node = layout.create_access_node(self._field_idx, self._access_node)
            self._access_node = node
        else:
            self._access_node = create_generic_access_node(self._field_idx)
        return self._access_node


class FieldReadNode(_AbstractFieldNode):
    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        assert isinstance(self_obj, ObjectWithLayout)

        layout = self_obj.get_object_layout()
        location = self._lookup(layout, self_obj)
        return location.read_fn(location, self_obj)


class FieldWriteNode(_AbstractFieldNode):

    _immutable_fields_ = ["_value_exp?"]
    _child_nodes_ = ["_value_exp"]

    def __init__(self, self_exp, value_exp, field_idx, source_section):
        _AbstractFieldNode.__init__(self, self_exp, field_idx, source_section)
        self._value_exp = self.adopt_child(value_exp)

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        value = self._value_exp.execute(frame)
        assert isinstance(self_obj, ObjectWithLayout)
        assert isinstance(value, AbstractObject)

        layout = self_obj.get_object_layout()
        location = self._lookup(layout, self_obj)

        try:
            location.write_fn(location, self_obj, value)
            return value
        except UninitializedStorageLocationException:
            self_obj.update_layout_with_initialized_field(
                self._field_idx, value.__class__
            )
        except GeneralizeStorageLocationException:
            self_obj.update_layout_with_generalized_field(self._field_idx)

        self_obj.set_field_after_layout_change(self._field_idx, value)
        return value


def create_read_node(self_exp, index, source_section=None):
    return FieldReadNode(self_exp, index, source_section)


def create_write_node(self_exp, value_exp, index, source_section=None):
    return FieldWriteNode(self_exp, value_exp, index, source_section)
