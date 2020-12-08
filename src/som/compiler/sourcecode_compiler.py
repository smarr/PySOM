import os
from rlib.streamio import open_file_as_stream
from rlib.string_stream    import StringStream

from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter

if is_ast_interpreter():
    from som.compiler.ast.parser import Parser
else:
    from som.compiler.bc.parser import Parser


def compile_class_from_file(path, filename, system_class, universe):
    return _SourcecodeCompiler().compile(path, filename, system_class, universe)


def compile_class_from_string(stmt, system_class, universe):
    return _SourcecodeCompiler().compile_class_string(stmt, system_class,
                                                      universe)


class _SourcecodeCompiler(object):

    def __init__(self):
        self._parser = None

    def compile(self, path, filename, system_class, universe):
        fname = path + os.sep + filename + ".som"

        try:
            input_file = open_file_as_stream(fname, "r")
            try:
                self._parser = Parser(input_file, fname, universe)
                result = self._compile(system_class, universe)
            finally:
                input_file.close()
        except OSError:
            raise IOError()

        cname = result.get_name()
        cnameC = cname.get_embedded_string()

        if filename != cnameC:
            from som.vm.universe import error_println
            error_println("File name %s does not match class name %s."
                          % (filename, cnameC))
            universe.exit(1)

        return result

    def compile_class_string(self, stream, system_class, universe):
        self._parser = Parser(StringStream(stream), "$str", universe)

        result = self._compile(system_class, universe)
        return result

    def _compile(self, system_class, universe):
        cgc = ClassGenerationContext(universe)

        result = system_class
        self._parser.classdef(cgc)

        if not system_class:
            result = cgc.assemble()
        else:
            cgc.assemble_system_class(result)

        return result
