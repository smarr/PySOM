from collections import OrderedDict

from rtruffle.source_section import SourceSection

from .variable import Argument, Local
from ..method_generation_context import MethodGenerationContextBase

from ...interpreter.ast.nodes.field_node import create_write_node, create_read_node
from ...interpreter.ast.nodes.global_read_node import create_global_node
from ...interpreter.ast.nodes.return_non_local_node import CatchNonLocalReturnNode
from ...interpreter.ast.invokable import Invokable

from ...vmobjects.primitive import empty_primitive
from ...vmobjects.method_ast import AstMethod


class MethodGenerationContext(MethodGenerationContextBase):
    def __init__(self, universe, outer=None):
        MethodGenerationContextBase.__init__(
            self, universe, outer, OrderedDict(), OrderedDict()
        )

        self._embedded_block_methods = []

        # does non-local return, directly or indirectly via a nested block
        self.throws_non_local_return = False

        self.needs_to_catch_non_local_returns = False
        self._accesses_variables_of_outer_context = False

    def add_embedded_block_method(self, block_method):
        self._embedded_block_methods.append(block_method)

    def make_catch_non_local_return(self):
        self.throws_non_local_return = True
        ctx = self._mark_outer_contexts_to_require_context_and_get_root_context()

        assert ctx is not None
        ctx.needs_to_catch_non_local_returns = True

    def requires_context(self):
        return self.throws_non_local_return or self._accesses_variables_of_outer_context

    def _mark_outer_contexts_to_require_context_and_get_root_context(self):
        ctx = self.outer_genc
        while ctx.outer_genc is not None:
            ctx.throws_non_local_return = True
            ctx = ctx.outer_genc
        return ctx

    @staticmethod
    def _separate_variables(variables, only_local_access, non_local_access):
        for var in variables:
            if var.is_accessed_out_of_context():
                var.set_access_index(len(non_local_access))
                non_local_access.append(var)
            elif only_local_access is not None:
                var.set_access_index(len(only_local_access))
                only_local_access.append(var)

    @staticmethod
    def _add_argument_initialization(method_body):
        return method_body
        # TODO: see whether that has any for of benefit, or whether that is
        # really just for the partial evaluator, that knows a certain pattern

        # writes = [LocalVariableWriteNode(arg.get_frame_idx(),
        #                                  ArgumentReadNode(arg.get_frame_idx()))
        #           for arg in self._arguments.values()]
        # return ArgumentInitializationNode(writes, method_body,
        #                                   method_body.get_source_section())

    def assemble(self, method_body):
        if self._primitive:
            return empty_primitive(self._signature.get_embedded_string(), self.universe)

        # local_args     = []
        non_local_args = []
        local_tmps = []
        non_local_tmps = []
        self._separate_variables(
            [arg for arg in self._arguments.values() if not arg.is_self()],
            None,
            non_local_args,
        )
        self._separate_variables(self._locals.values(), local_tmps, non_local_tmps)

        arg_mapping = [arg.get_argument_index() for arg in non_local_args]

        if self.needs_to_catch_non_local_returns:
            method_body = CatchNonLocalReturnNode(
                method_body, method_body.source_section
            )

        method_body = self._add_argument_initialization(method_body)
        method = Invokable(
            self._get_source_section_for_method(method_body),
            method_body,
            arg_mapping,
            len(local_tmps),
            len(non_local_tmps),
            self.universe,
        )
        return AstMethod(
            self._signature,
            method,
            # copy list to make it immutable for RPython
            self._embedded_block_methods[:],
            self.universe,
        )

    def _get_source_section_for_method(self, expr):
        src_body = expr.source_section
        assert isinstance(src_body, SourceSection)
        src_method = SourceSection(
            identifier="%s>>#%s"
            % (
                self.holder.name.get_embedded_string(),
                self._signature.get_embedded_string(),
            ),
            source_section=src_body,
        )
        return src_method

    def add_argument(self, arg):
        if (arg == "self" or arg == "$blockSelf") and len(self._arguments) > 0:
            raise RuntimeError(
                "The self argument always has to be the first " "argument of a method"
            )
        argument = Argument(arg, len(self._arguments) - 1)
        self._arguments[arg] = argument

    def add_argument_if_absent(self, arg):
        if arg in self._arguments:
            return
        self.add_argument(arg)

    def add_local(self, local):
        self._locals[local] = Local(local, len(self._locals))

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

    def _get_self_read(self):
        return self.get_variable("self").get_read_node(self.get_context_level("self"))

    def get_object_field_read(self, field_name):
        if not self.has_field(field_name):
            return None
        return create_read_node(self._get_self_read(), self.get_field_index(field_name))

    def get_global_read(self, var_name):
        return create_global_node(var_name, self.universe, None)

    def get_object_field_write(self, field_name, exp):
        if not self.has_field(field_name):
            return None
        return create_write_node(
            self._get_self_read(), exp, self.get_field_index(field_name)
        )

    def __str__(self):
        return "MethodGenC(%s>>%s)" % (
            self.holder.get_name().get_string,
            self._signature,
        )
