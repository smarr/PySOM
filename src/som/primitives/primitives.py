class Primitives(object):

    def __init__(self, universe):
        self._universe = universe
        self._holder = None

    def install_primitives_in(self, value):
        # Save a reference to the holder class
        self._holder = value

        # Install the primitives from this primitives class
        self.install_primitives()

    def install_primitives(self):
        raise NotImplementedError()

    def _install_instance_primitive(self, primitive, warn_if_not_existing = False):
        # Install the given primitive as an instance primitive in the holder class
        self._holder.add_instance_primitive(primitive, warn_if_not_existing)

    def _install_class_primitive(self, primitive, warn_if_not_existing = False):
        # Install the given primitive as an instance primitive in the class of
        # the holder class
        self._holder.get_class(
            self._universe).add_instance_primitive(primitive, warn_if_not_existing)
