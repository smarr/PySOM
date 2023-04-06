from som.interpreter.ast.nodes.field_node import AbstractFieldNode


class FieldIncrementNode(AbstractFieldNode):
    _immutable_fields_ = ["_inc_value"]

    def __init__(self, self_exp, field_idx, inc_value, source_section):
        AbstractFieldNode.__init__(self, self_exp, field_idx, source_section)
        self._inc_value = inc_value

    def execute(self, frame):
        self_obj = self._self_exp.execute(frame)
        return self_obj.inc_field(self.field_idx, self._inc_value)
