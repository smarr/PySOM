import time

from rlib import rgc, jit

from som.primitives.primitives import Primitives
from som.vm.globals import nilObject, trueObject, falseObject
from som.vm.universe import get_current, std_print, std_println, error_print, error_println
from som.vmobjects.primitive import UnaryPrimitive, BinaryPrimitive, TernaryPrimitive


def _load(rcvr, arg):
    result = get_current().load_class(arg)
    return result if result else nilObject


def _exit(rcvr, error):
    return get_current().exit(error.get_embedded_integer())


def _global(rcvr, argument):
    result = get_current().get_global(argument)
    return result if result else nilObject


def _has_global(rcvr, arg):
    if get_current().has_global(arg):
        return trueObject
    else:
        return falseObject


def _global_put(rcvr, argument, value):
    get_current().set_global(argument, value)
    return value


def _print_string(rcvr, argument):
    std_print(argument.get_embedded_string())
    return rcvr


def _print_newline(rcvr):
    std_println()
    return rcvr


def _error_print(rcvr, string):
    error_print(string.get_embedded_string())
    return rcvr


def _error_println(rcvr, string):
    error_println(string.get_embedded_string())
    return rcvr


def _time(rcvr):
    from som.vmobjects.integer import Integer
    since_start = time.time() - get_current().start_time
    return Integer(int(since_start * 1000))


def _ticks(rcvr):
    from som.vmobjects.integer import Integer
    since_start = time.time() - get_current().start_time
    return Integer(int(since_start * 1000000))


@jit.dont_look_inside
def _full_gc(rcvr):
    rgc.collect()
    return trueObject


class SystemPrimitivesBase(Primitives):

    def install_primitives(self):
        self._install_instance_primitive(BinaryPrimitive("load:", self._universe, _load))
        self._install_instance_primitive(BinaryPrimitive("exit:", self._universe, _exit))
        self._install_instance_primitive(BinaryPrimitive("hasGlobal:", self._universe, _has_global))
        self._install_instance_primitive(BinaryPrimitive("global:", self._universe, _global))
        self._install_instance_primitive(TernaryPrimitive("global:put:", self._universe, _global_put))
        self._install_instance_primitive(BinaryPrimitive("printString:", self._universe, _print_string))
        self._install_instance_primitive(UnaryPrimitive("printNewline", self._universe, _print_newline))
        self._install_instance_primitive(BinaryPrimitive("errorPrint:", self._universe, _error_print))
        self._install_instance_primitive(BinaryPrimitive("errorPrintln:", self._universe, _error_println))

        self._install_instance_primitive(UnaryPrimitive("time", self._universe, _time))
        self._install_instance_primitive(UnaryPrimitive("ticks", self._universe, _ticks))
        self._install_instance_primitive(UnaryPrimitive("fullGC", self._universe, _full_gc))
