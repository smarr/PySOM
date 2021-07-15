class AbstractObject(object):
    def __init__(self):
        pass

    def get_class(self, universe):
        raise NotImplementedError("Subclasses need to implement get_class(universe).")

    def get_object_layout(self, universe):
        raise NotImplementedError(
            "Subclasses need to implement get_object_layout(universe)."
        )

    @staticmethod
    def is_invokable():
        return False

    def __str__(self):
        from som.vm.current import current_universe

        return "a " + self.get_class(current_universe).get_name().get_embedded_string()
