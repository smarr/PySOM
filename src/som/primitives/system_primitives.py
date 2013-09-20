from som.primitives.primitives import Primitives
from som.vmobjects.primitive   import Primitive

from som.vm.universe import std_print, std_println

import time

class SystemPrimitives(Primitives):
    
    def __init__(self, universe):
        Primitives.__init__(self, universe)
        self._start_time = time.time() # a float of the time in seconds
    
    def install_primitives(self):
        def _load(ivkbl, frame, interpreter):
            argument = frame.pop()
            frame.pop() # not required
            result = self._universe.load_class(argument)
            frame.push(result if result else self._universe.nilObject)
        self._install_instance_primitive(Primitive("load:", self._universe, _load))

        def _exit(ivkbl, frame, interpreter):
            error = frame.pop()
            self._universe.exit(error.get_embedded_integer())
        self._install_instance_primitive(Primitive("exit:", self._universe, _exit))

        def _global(ivkbl, frame, interpreter):
            argument = frame.pop()
            frame.pop() # not required
            result = self._universe.get_global(argument)
            frame.push(result if result else self._universe.nilObject)
        self._install_instance_primitive(Primitive("global:", self._universe, _global))

        def _global_put(ivkbl, frame, interpreter):
            value    = frame.pop()
            argument = frame.pop()
            self._universe.set_global(argument, value)
        self._install_instance_primitive(Primitive("global:put:", self._universe, _global_put))

        def _print_string(ivkbl, frame, interpreter):
            argument = frame.pop()
            std_print(argument.get_embedded_string())
        self._install_instance_primitive(Primitive("printString:", self._universe, _print_string))

        def _print_newline(ivkbl, frame, interpreter):
            std_println()
        self._install_instance_primitive(Primitive("printNewline", self._universe, _print_newline))

        def _time(ivkbl, frame, interpreter):
            frame.pop() # ignore
            _time = time.time() - self._start_time
            frame.push(self._universe.new_integer(_time * 1000))
        self._install_instance_primitive(Primitive("time", self._universe, _time))

        def _ticks(ivkbl, frame, interpreter):
            frame.pop() # ignore
            _time = time.time() - self._start_time
            frame.push(self._universe.new_integer(_time * 1000000))
        self._install_instance_primitive(Primitive("ticks", self._universe, _ticks))

        def _fullGC(ivkbl, frame, interpreter):
            # naught - GC is entirely left to Python
            pass
        self._install_instance_primitive(Primitive("fullGC", self._universe, _fullGC))
