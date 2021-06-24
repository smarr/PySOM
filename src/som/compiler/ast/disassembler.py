from som.vm.universe import error_print, error_println


def dump(clazz):
    for inv in clazz.get_instance_invokables_for_disassembler():
        # output header and skip if the Invokable is a Primitive
        error_print(str(clazz.get_name()) + ">>" + str(inv.get_signature()) + " = ")

        if inv.is_primitive():
            error_println("<primitive>")
            continue

        # output actual method
        dump_method(inv, "\t")


def dump_method(_, indent):
    error_println("(")
    error_println(indent + indent + "TODO")
    error_println(indent + ")")
