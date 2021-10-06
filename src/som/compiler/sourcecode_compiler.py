import os
from rlib.streamio import open_file_as_stream
from rlib.string_stream import StringStream

from som.compiler.class_generation_context import ClassGenerationContext

from som.compiler.ast.parser import Parser


def compile_class_from_file(path, filename, system_class, universe):
    fname = path + os.sep + filename + ".som"

    try:
        input_file = open_file_as_stream(fname, "r")
        try:
            parser = Parser(input_file, fname, universe)
            result = _compile(parser, system_class, universe)
        finally:
            input_file.close()
    except OSError:
        raise IOError()

    cname = result.get_name()
    cname_str = cname.get_embedded_string()

    if filename != cname_str:
        from som.vm.universe import error_println

        error_println(
            "File name %s does not match class name %s." % (filename, cname_str)
        )
        universe.exit(1)

    return result


def compile_class_from_string(stream, system_class, universe):
    parser = Parser(StringStream(stream), "$str", universe)
    result = _compile(parser, system_class, universe)
    return result


def _compile(parser, system_class, universe):
    cgc = ClassGenerationContext(universe)

    result = system_class
    parser.classdef(cgc)

    if not system_class:
        result = cgc.assemble()
    else:
        cgc.assemble_system_class(result)

    return result
