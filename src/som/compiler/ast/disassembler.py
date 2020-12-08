from som.vm.universe import error_print, error_println


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
    error_println(indent + indent + "TODO")
    error_println(indent + ")")
