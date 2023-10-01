from rlib.exit import Exit
from rlib.objectmodel import we_are_translated
from rlib.osext import raw_input
from som.compiler.parse_error import ParseError
from som.vm.globals import nilObject
from som.vm.symbols import symbol_for


class Shell(object):
    def __init__(self, universe):
        self.universe = universe

    def start(self):
        from som.vm.universe import std_println, error_println

        counter = 0
        it = nilObject

        std_println('SOM Shell. Type "quit" to exit.\n')

        while True:
            try:
                # Read a statement from the keyboard
                stmt = raw_input(b"---> ")
                if stmt == "quit" or stmt == "":
                    return it
                if stmt == "\n":
                    continue

                # Generate a temporary class with a run method
                stmt = (
                    "Shell_Class_"
                    + str(counter)
                    + " = ( run: it = ( | tmp | tmp := ("
                    + stmt
                    + " ). 'it = ' print. ^tmp println ) )"
                )
                counter += 1

                # Compile and load the newly generated class
                shell_class = self.universe.load_shell_class(stmt)

                # If success
                if shell_class:
                    shell_object = self.universe.new_instance(shell_class)
                    shell_method = shell_class.lookup_invokable(symbol_for("run:"))

                    it = shell_method.invoke_2(shell_object, it)
            except ParseError as ex:
                error_println(str(ex))
            except Exit as ex:
                raise ex
            except Exception as ex:  # pylint: disable=broad-except
                if not we_are_translated():  # this cannot be done in rpython
                    import traceback

                    traceback.print_exc()
                error_println("Caught exception: %s" % ex)
