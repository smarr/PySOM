from som.primitives.primitives import Primitives
from som.vmobjects.primitive   import Primitive


def _restart(ivkbl, rcvr, args):
    raise RuntimeError("Restart primitive is not supported, #whileTrue: "
                       "and #whileTrue: are intrisified so that #restart "
                       "is not needed.")


class BlockPrimitives(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(Primitive("restart",
                                                   self._universe, _restart))
