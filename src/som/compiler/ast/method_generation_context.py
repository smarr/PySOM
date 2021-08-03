from rtruffle.source_section import SourceSection

from som.compiler.method_generation_context import MethodGenerationContextBase

from som.interpreter.ast.nodes.field_node import create_write_node, create_read_node
from som.interpreter.ast.nodes.global_read_node import create_global_node
from som.interpreter.ast.nodes.return_non_local_node import CatchNonLocalReturnNode

from som.vmobjects.primitive import empty_primitive
from som.vmobjects.method_ast import AstMethod


class MethodGenerationContext(MethodGenerationContextBase):
    def __init__(self, universe, holder, outer):
        MethodGenerationContextBase.__init__(self, universe, holder, outer)

        self._embedded_block_methods = []

    def add_embedded_block_method(self, block_method):
        self._embedded_block_methods.append(block_method)

    def assemble(self, method_body):
        if self._primitive:
            return empty_primitive(self.signature.get_embedded_string())

        if self.needs_to_catch_non_local_returns:
            method_body = CatchNonLocalReturnNode(
                method_body, method_body.source_section
            )

        trivial_method = method_body.create_trivial_method(self.signature)
        if trivial_method is not None:
            return trivial_method

        arg_inner_access, size_frame, size_inner = self.prepare_frame()

        return AstMethod(
            self.signature,
            method_body,
            arg_inner_access,
            size_frame,
            size_inner,
            # copy list to make it immutable for RPython
            self._embedded_block_methods[:],
            self._get_source_section_for_method(method_body),
            self.lexical_scope,
        )

    def _get_source_section_for_method(self, expr):
        src_body = expr.source_section
        assert isinstance(src_body, SourceSection)
        src_method = SourceSection(
            identifier="%s>>#%s"
            % (
                self.holder.name.get_embedded_string(),
                self.signature.get_embedded_string(),
            ),
            source_section=src_body,
        )
        return src_method

    def get_outer_self_context_level(self):
        level = 0
        ctx = self.outer_genc
        while ctx is not None:
            ctx = ctx.outer_genc
            level += 1
        return level

    def get_context_level(self, var_name):
        if var_name in self._locals or var_name in self._arguments:
            return 0
        assert self.outer_genc is not None
        return 1 + self.outer_genc.get_context_level(var_name)

    def get_variable(self, var_name):
        if var_name in self._locals:
            return self._locals[var_name]

        if var_name in self._arguments:
            return self._arguments[var_name]

        if self.outer_genc:
            outer_var = self.outer_genc.get_variable(var_name)
            if outer_var:
                self._accesses_variables_of_outer_context = True
                return outer_var
        return None

    def get_local(self, var_name):
        if var_name in self._locals:
            return self._locals[var_name]

        if self.outer_genc:
            outer_local = self.outer_genc.get_local(var_name)
            if outer_local:
                self._accesses_variables_of_outer_context = True
                return outer_local
        return None

    def get_self_read(self):
        return self.get_variable("self").get_read_node(self.get_context_level("self"))

    def get_object_field_read(self, field_name):
        if not self.has_field(field_name):
            return None
        return create_read_node(self.get_self_read(), self.get_field_index(field_name))

    def get_global_read(self, var_name):
        return create_global_node(var_name, self.universe, self, None)

    def get_object_field_write(self, field_name, exp):
        if not self.has_field(field_name):
            return None
        return create_write_node(
            self.get_self_read(), exp, self.get_field_index(field_name)
        )
