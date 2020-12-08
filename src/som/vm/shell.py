from rlib.objectmodel import we_are_translated
from rlib.osext import raw_input

from som.interpreter.bc.frame import create_frame
from som.vm.globals import nilObject


class _Shell(object):

    def __init__(self, universe):
        self._universe = universe

    def start(self):
        from som.vm.universe import std_println, error_println
        counter = 0
        it = nilObject

        std_println("SOM Shell. Type \"quit\" to exit.\n")

        while True:
            try:
                # Read a statement from the keyboard
                stmt = raw_input("---> ")
                if stmt == "quit" or stmt == "":
                    return it
                elif stmt == "\n":
                    continue

                # Generate a temporary class with a run method
                stmt = ("Shell_Class_" + str(counter) +
                        " = ( run: it = ( | tmp | tmp := (" + stmt +
                        " ). 'it = ' print. ^tmp println ) )")
                counter += 1

                # Compile and load the newly generated class
                shell_class = self._universe.load_shell_class(stmt)

                # If success
                if shell_class:
                    shell_object = self._universe.new_instance(shell_class)
                    shell_method = shell_class.lookup_invokable(
                        self._universe.symbol_for("run:"))

                    it = self._exec(shell_object, shell_method, it)
            except Exception as e:
                if not we_are_translated():  # this cannot be done in rpython
                    import traceback
                    traceback.print_exc()
                error_println("Caught exception: %s" % e)


class AstShell(_Shell):

    def _exec(self, shell_object, shell_method, it):
        return shell_method.invoke(shell_object, [it])


class BcShell(_Shell):

    def __init__(self, universe, interpreter, bootstrap_method):
        _Shell.__init__(self, universe)
        self._interpreter = interpreter
        self._bootstrap_method = bootstrap_method
        # Create a fake bootstrap frame
        self._current_frame = create_frame(None, self._bootstrap_method, None)

    def _exec(self, shell_object, shell_method, it):
        self._current_frame.reset_stack_pointer()
        self._current_frame.push(shell_object)

        # Push the old value of "it" on the stack
        self._current_frame.push(it)

        # Invoke the run method
        shell_method.invoke(self._current_frame, self._interpreter)

        return self._current_frame.pop()
