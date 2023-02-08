from rlib.jit import promote

from som.vmobjects.abstract_object import AbstractObject


class ObjectWithoutFields(AbstractObject):
    _immutable_fields_ = ["_object_layout?"]

    def __init__(self, layout):  # pylint: disable=W
        self._object_layout = layout

    def get_class(self, universe):
        assert self._object_layout is not None
        return self._object_layout.for_class

    def get_object_layout(self, _universe):
        return promote(self._object_layout)

    def set_class(self, clazz):
        layout = clazz.get_layout_for_instances()
        assert layout is not None
        self._object_layout = layout

    def get_number_of_fields(self):
        return 0

    def __str__(self):
        from som.vm.globals import nilObject, trueObject, falseObject

        if self is nilObject:
            return "nil"
        if self is trueObject:
            return "true"
        if self is falseObject:
            return "false"
        return AbstractObject.__str__(self)
