class AbstractObject(object):

    def __init__(self):
        pass

    def get_class(self, universe):
        raise NotImplementedError("Subclasses need to implement get_class(universe).")

    @staticmethod
    def is_invokable():
        return False

    def __str__(self):
        from som.vm.universe import get_current
        return "a " + self.get_class(get_current()).get_name().get_embedded_string()
