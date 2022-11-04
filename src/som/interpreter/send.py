from som.vm.symbols import symbol_for


def lookup_and_send_2(receiver, arg, selector_string):
    from som.vm.current import current_universe

    selector = symbol_for(selector_string)
    invokable = receiver.get_class(current_universe).lookup_invokable(selector)

    return invokable.invoke_2(receiver, arg)


def lookup_and_send_3(receiver, arg1, arg2, selector_string):
    from som.vm.current import current_universe

    selector = symbol_for(selector_string)
    invokable = receiver.get_class(current_universe).lookup_invokable(selector)
    return invokable.invoke_3(receiver, arg1, arg2)


def get_inline_cache_size(cache):
    size = 0
    while cache is not None:
        size += 1
        cache = cache.next_entry
    return size


def get_clean_inline_cache_and_size(cache):
    prev = None
    new_cache = cache
    size = 0

    while cache is not None:
        if not cache.expected_layout.is_latest:
            if prev is None:
                new_cache = cache.next_entry
            else:
                prev.next_entry = cache.next_entry
        else:
            prev = cache
            size += 1

        cache = cache.next_entry

    return new_cache, size
