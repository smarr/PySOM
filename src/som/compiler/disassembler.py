from som.interp_type import is_ast_interpreter

if is_ast_interpreter():
    from som.compiler.ast.disassembler import dump as d_fn
else:
    from som.compiler.bc.disassembler import dump as d_fn

dump = d_fn
