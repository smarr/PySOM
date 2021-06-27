def _init():
    from som.vm.universe import create_universe

    return create_universe()


current_universe = _init()
