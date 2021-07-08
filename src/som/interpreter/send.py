def lookup_and_send_2(receiver, arg, selector_string):
    from som.vm.current import current_universe

    selector = current_universe.symbol_for(selector_string)
    invokable = receiver.get_class(current_universe).lookup_invokable(selector)

    return invokable.invoke_2(receiver, arg)


def lookup_and_send_3(receiver, arg1, arg2, selector_string):
    from som.vm.current import current_universe

    selector = current_universe.symbol_for(selector_string)
    invokable = receiver.get_class(current_universe).lookup_invokable(selector)
    return invokable.invoke_3(receiver, arg1, arg2)
