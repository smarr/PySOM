from som.vm.universe import error_print, error_println, get_current
from som.interpreter.bc.bytecodes import bytecode_as_str, bytecode_length, Bytecodes


def dump(clazz):
    for i in range(0, clazz.get_number_of_instance_invokables()):
        inv = clazz.get_instance_invokable(i)

        # output header and skip if the Invokable is a Primitive
        error_print(str(clazz.get_name()) + ">>" +
                    str(inv.get_signature()) + " = ")

        if inv.is_primitive():
            error_println("<primitive>")
            continue

        # output actual method
        dump_method(inv, "\t")


def dump_method(m, indent):
    error_println("(")

    # output stack information
    error_println("%s<%d locals, %d stack, %d bc_count>" % (indent,
                           m.get_number_of_locals(),
                           m.get_maximum_number_of_stack_elements(),
                           m.get_number_of_bytecodes()))

    # output bytecodes
    b = 0
    while b < m.get_number_of_bytecodes():
        error_print(indent)

        # bytecode index
        if b < 10:  error_print(" ")
        if b < 100: error_print(" ")
        error_print(" %d:" % b)

        # mnemonic
        bytecode = m.get_bytecode(b)
        error_print(bytecode_as_str(bytecode) + "  ")

        # parameters (if any)
        if bytecode_length(bytecode) == 1:
            error_println()
            b += 1
            continue

        if bytecode == Bytecodes.push_local:
            error_println("local: " + str(m.get_bytecode(b + 1)) +
                                   ", context: " + str(m.get_bytecode(b + 2)))
        elif bytecode == Bytecodes.push_argument:
            error_println("argument: " + str(m.get_bytecode(b + 1)) +
                                   ", context " + str(m.get_bytecode(b + 2)))
        elif bytecode == Bytecodes.push_field:
            error_println("(index: " + str(m.get_bytecode(b + 1)) +
                                   ") field: " + str(m.get_holder().get_instance_field_name(m.get_bytecode(b + 1))))
        elif bytecode == Bytecodes.push_block:
            error_print("block: (index: " + str(m.get_bytecode(b + 1)) + ") ")
            dump_method(m.get_constant(b), indent + "\t")
        elif bytecode == Bytecodes.push_constant:
            constant = m.get_constant(b)
            error_println("(index: " + str(m.get_bytecode(b + 1)) +
                                   ") value: (" +
                                   str(constant.get_class(get_current()).get_name()) +
                                   ") " + str(constant))
        elif bytecode == Bytecodes.push_global:
            error_println("(index: " + str(m.get_bytecode(b + 1)) +
                                   ") value: " + str(m.get_constant(b)))
        elif bytecode == Bytecodes.pop_local:
            error_println("local: "     + str(m.get_bytecode(b + 1)) +
                                   ", context: " + str(m.get_bytecode(b + 2)))
        elif bytecode == Bytecodes.pop_argument:
            error_println("argument: "  + str(m.get_bytecode(b + 1)) +
                                   ", context: " + str(m.get_bytecode(b + 2)))
        elif bytecode == Bytecodes.pop_field:
            error_println("(index: "  + str(m.get_bytecode(b + 1)) +
                                   ") field: " + str(m.get_holder().get_instance_field_name(m.get_bytecode(b + 1))))
        elif bytecode == Bytecodes.send:
            error_println("(index: "      + str(m.get_bytecode(b + 1)) +
                                   ") signature: " + str(m.get_constant(b)))
        elif bytecode == Bytecodes.super_send:
            error_println("(index: "      + str(m.get_bytecode(b + 1)) +
                                   ") signature: " + str(m.get_constant(b)))
        else:
            error_println("<incorrect bytecode>")

        b += bytecode_length(m.get_bytecode(b))

    error_println(indent + ")")
