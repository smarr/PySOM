from som.interpreter.ast.nodes.contextual_node import ContextualNode
from som.interpreter.ast.nodes.dispatch import lookup_and_send
from som.interpreter.ast.nodes.expression_node import ExpressionNode

from som.interpreter.control_flow import ReturnException


class ReturnNonLocalNode(ContextualNode):

    _immutable_fields_ = ["_expr?", "universe"]
    _child_nodes_ = ["_expr"]

    def __init__(self, context_level, expr, universe, source_section=None):
        ContextualNode.__init__(self, context_level, source_section)
        self._expr = self.adopt_child(expr)
        self.universe = universe

    def execute(self, frame):
        result = self._expr.execute(frame)
        block = self.determine_block(frame)

        if block.is_outer_on_stack():
            raise ReturnException(result, block.get_on_stack_marker())
        block = frame.get_self()
        outer_self = block.get_outer_self()
        return self.send_escaped_block(outer_self, block, self.universe)

    @staticmethod
    def send_escaped_block(receiver, block, universe):
        arguments = [block]
        return lookup_and_send(receiver, "escapedBlock:", arguments, universe)


class CatchNonLocalReturnNode(ExpressionNode):

    _immutable_fields_ = ["_method_body?"]
    _child_nodes_ = ["_method_body"]

    def __init__(self, method_body, source_section=None):
        ExpressionNode.__init__(self, source_section)
        self._method_body = self.adopt_child(method_body)

    def execute(self, frame):
        marker = frame.get_on_stack_marker()
        try:
            return self._method_body.execute(frame)
        except ReturnException as ex:
            if not ex.has_reached_target(marker):
                raise ex
            return ex.get_result()
        finally:
            marker.mark_as_no_longer_on_stack()
