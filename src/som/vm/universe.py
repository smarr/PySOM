from rlib.debug import make_sure_not_resized
from rlib import jit
from rlib.string_stream import encode_to_bytes


from som.compiler.bc.method_generation_context import create_bootstrap_method
from som.interpreter.bc.interpreter import Interpreter
from som.interpreter.bc.frame import create_bootstrap_frame

from som.interp_type import is_ast_interpreter

if is_ast_interpreter():
    from som.vmobjects.object_with_layout import ObjectWithLayout as Object
    from som.vmobjects.array_strategy     import Array
    from som.vmobjects.block_ast          import block_evaluation_primitive
    from som.vm.shell                     import AstShell
else:
    from som.vmobjects.object   import Object
    from som.vmobjects.array    import Array
    from som.vmobjects.block_bc import block_evaluation_primitive
    from som.vm.shell           import BcShell

from som.vmobjects.clazz         import Class
from som.vmobjects.object_without_fields import ObjectWithoutFields
from som.vmobjects.symbol        import Symbol
from som.vmobjects.string        import String

from som.vm.globals import nilObject, trueObject, falseObject

import som.compiler.sourcecode_compiler as sourcecode_compiler

import os
import time


from rlib.exit  import Exit
from rlib.osext import path_split


class Assoc(object):

    _immutable_fields_ = ["_global_name", "_value?"]

    def __init__(self, global_name, value):
        self._global_name = global_name
        self._value       = value

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def __str__(self):
        return "(%s => %s)" % (self._global_name, self._value)


class Universe(object):

    _immutable_fields_ = [
            "objectClass",
            "classClass",
            "metaclassClass",
            "nilClass",
            "integerClass",
            "arrayClass",
            "methodClass",
            "symbolClass",
            "primitiveClass",
            "systemClass",
            "blockClass",
            "blockClasses[*]",
            "stringClass",
            "doubleClass",
            "_symbol_table",
            "_globals",
            "_object_system_initialized"]

    def __init__(self, avoid_exit = False):
        self._symbol_table   = {}
        self._globals        = {}

        self.objectClass    = None
        self.classClass     = None
        self.metaclassClass = None

        self.nilClass       = None
        self.integerClass   = None
        self.arrayClass     = None
        self.methodClass    = None
        self.symbolClass    = None
        self.primitiveClass = None
        self.systemClass    = None
        self.blockClass     = None
        self.blockClasses   = None
        self.stringClass    = None
        self.doubleClass    = None

        self._last_exit_code = 0
        self._avoid_exit     = avoid_exit
        self._dump_bytecodes = False
        self.classpath       = None
        self.start_time      = time.time()  # a float of the time in seconds
        self._object_system_initialized = False

    def exit(self, error_code):
        if self._avoid_exit:
            self._last_exit_code = error_code
        else:
            raise Exit(error_code)

    def last_exit_code(self):
        return self._last_exit_code

    def execute_method(self, class_name, selector):
        self._initialize_object_system()

        clazz = self.load_class(self.symbol_for(class_name))
        if clazz is None:
            raise Exception("Class " + class_name + " could not be loaded.")

        # Lookup the invokable on class
        invokable = clazz.get_class(self).lookup_invokable(self.symbol_for(selector))
        if invokable is None:
            raise Exception("Lookup of " + selector + " failed in class " + class_name)

        return self._start_method_execution(clazz, invokable)

    def interpret(self, arguments):
        # Check for command line switches
        arguments = self.handle_arguments(arguments)

        # Initialize the known universe
        system_object = self._initialize_object_system()

        # Start the shell if no filename is given
        if len(arguments) == 0:
            return self._start_shell()
        else:
            arguments_array = self.new_array_with_strings(arguments)
            initialize = self.systemClass.lookup_invokable(self.symbol_for("initialize:"))
            return self._start_execution(system_object, initialize, arguments_array)

    def handle_arguments(self, arguments):
        got_classpath  = False
        remaining_args = []
        saw_others = False

        i = 0
        while i < len(arguments):
            if arguments[i] == "-cp" and not saw_others:
                if i + 1 >= len(arguments):
                    self._print_usage_and_exit()
                self.setup_classpath(arguments[i + 1])
                i += 1    # skip class path
                got_classpath = True
            elif arguments[i] == "-d" and not saw_others:
                self._dump_bytecodes = True
            elif arguments[i] in ["-h", "--help", "-?"] and not saw_others:
                self._print_usage_and_exit()
            else:
                saw_others = True
                remaining_args.append(arguments[i])
            i += 1

        if not got_classpath:
            # Get the default class path of the appropriate size
            self.classpath = self._default_classpath()

        # check remaining args for class paths, and strip file extension
        if remaining_args:
            split = self._get_path_class_ext(remaining_args[0])

            if split[0] != "":  # there was a path
                self.classpath.insert(0, split[0])

            remaining_args[0] = split[1]

        return remaining_args

    def setup_classpath(self, cp):
        self.classpath = cp.split(os.pathsep)

    @staticmethod
    def _default_classpath():
        return ['.']

    # take argument of the form "../foo/Test.som" and return
    # "../foo", "Test", "som"
    @staticmethod
    def _get_path_class_ext(path):
        return path_split(path)

    def _print_usage_and_exit(self):
        # Print the usage
        std_println("Usage: som [-options] [args...]                          ")
        std_println("                                                         ")
        std_println("where options include:                                   ")
        std_println("    -cp <directories separated by " + os.pathsep     + ">")
        std_println("        set search path for application classes")
        std_println("    -d  enable disassembling")
        std_println("    -h  print this help")

        # Exit
        self.exit(0)

    def _initialize_object_system(self):
        # Allocate the Metaclass classes
        self.metaclassClass = self.new_metaclass_class()

        # Allocate the rest of the system classes
        self.objectClass     = self.new_system_class()
        self.nilClass        = self.new_system_class()
        self.classClass      = self.new_system_class()
        self.arrayClass      = self.new_system_class()
        self.symbolClass     = self.new_system_class()
        self.methodClass     = self.new_system_class()
        self.integerClass    = self.new_system_class()
        self.primitiveClass  = self.new_system_class()
        self.stringClass     = self.new_system_class()
        self.doubleClass     = self.new_system_class()

        # Setup the class reference for the nil object
        nilObject.set_class(self.nilClass)

        # Initialize the system classes
        self._initialize_system_class(self.objectClass,                 None, "Object")
        self._initialize_system_class(self.classClass,      self.objectClass, "Class")
        self._initialize_system_class(self.metaclassClass,   self.classClass, "Metaclass")
        self._initialize_system_class(self.nilClass,        self.objectClass, "Nil")
        self._initialize_system_class(self.arrayClass,      self.objectClass, "Array")
        self._initialize_system_class(self.methodClass,     self.objectClass, "Method")
        self._initialize_system_class(self.integerClass,    self.objectClass, "Integer")
        self._initialize_system_class(self.primitiveClass,  self.objectClass, "Primitive")
        self._initialize_system_class(self.stringClass,     self.objectClass, "String")
        self._initialize_system_class(self.symbolClass,     self.stringClass, "Symbol")
        self._initialize_system_class(self.doubleClass,     self.objectClass, "Double")

        # Load methods and fields into the system classes
        self._load_system_class(self.objectClass)
        self._load_system_class(self.classClass)
        self._load_system_class(self.metaclassClass)
        self._load_system_class(self.nilClass)
        self._load_system_class(self.arrayClass)
        self._load_system_class(self.methodClass)
        self._load_system_class(self.symbolClass)
        self._load_system_class(self.integerClass)
        self._load_system_class(self.primitiveClass)
        self._load_system_class(self.stringClass)
        self._load_system_class(self.doubleClass)

        # Load the generic block class
        self.blockClass = self.load_class(self.symbol_for("Block"))

        # Setup the true and false objects
        trueClassName    = self.symbol_for("True")
        trueClass        = self.load_class(trueClassName)
        trueClass.load_primitives(False)
        trueObject.set_class(trueClass)

        falseClassName   = self.symbol_for("False")
        falseClass       = self.load_class(falseClassName)
        falseClass.load_primitives(False)
        falseObject.set_class(falseClass)

        # Load the system class and create an instance of it
        self.systemClass = self.load_class(self.symbol_for("System"))
        system_object = self.new_instance(self.systemClass)

        # Put special objects and classes into the dictionary of globals
        self.set_global(self.symbol_for("nil"),    nilObject)
        self.set_global(self.symbol_for("true"),   trueObject)
        self.set_global(self.symbol_for("false"),  falseObject)
        self.set_global(self.symbol_for("system"), system_object)
        self.set_global(self.symbol_for("System"), self.systemClass)
        self.set_global(self.symbol_for("Block"),  self.blockClass)

        self.set_global(self.symbol_for("Nil"),    self.nilClass)

        self.set_global( trueClassName,  trueClass)
        self.set_global(falseClassName, falseClass)

        self.blockClasses = [self.blockClass] + \
                [self._make_block_class(i) for i in [1, 2, 3]]

        self._object_system_initialized = True
        return system_object

    def is_object_system_initialized(self):
        return self._object_system_initialized

    @jit.elidable
    def symbol_for(self, string):
        # Lookup the symbol in the symbol table
        result = self._symbol_table.get(string, None)
        if result is not None:
            return result

        # Create a new symbol and return it
        result = self._new_symbol(string)
        return result

    @staticmethod
    def new_array_with_length(length):
        return Array.from_size(length)

    @staticmethod
    def new_array_from_list(values):
        make_sure_not_resized(values)
        return Array.from_values(values)

    @staticmethod
    def new_array_with_strings(strings):
        values = [String(s) for s in strings]
        return Array.from_objects(values)

    def new_class(self, class_class):
        # Allocate a new class and set its class to be the given class class
        return Class(self, class_class.get_number_of_instance_fields(), class_class)

    @staticmethod
    def new_instance(instance_class):
        num_fields = instance_class.get_number_of_instance_fields()
        if num_fields == 0:
            return ObjectWithoutFields(instance_class)
        else:
            return Object(instance_class, num_fields)

    def new_metaclass_class(self):
        # Allocate the metaclass classes
        class_class = Class(self, 0, None)
        result = Class(self, 0, class_class)

        # Setup the metaclass hierarchy
        result.get_class(self).set_class(result)
        return result

    def _new_symbol(self, string):
        result = Symbol(string)

        # Insert the new symbol into the symbol table
        self._symbol_table[string] = result
        return result

    def new_system_class(self):
        # Allocate the new system class
        system_class_class = Class(self, 0, None)
        system_class = Class(self, 0, system_class_class)

        # Setup the metaclass hierarchy
        system_class.get_class(self).set_class(self.metaclassClass)
        return system_class

    def _initialize_system_class(self, system_class, super_class, name):
        # Initialize the superclass hierarchy
        if super_class:
            system_class.set_super_class(super_class)
            system_class.get_class(self).set_super_class(
                super_class.get_class(self))
        else:
            system_class.get_class(self).set_super_class(self.classClass)

        # Initialize the array of instance fields
        system_class.set_instance_fields(self.new_array_with_length(0))
        system_class.get_class(self).set_instance_fields(self.new_array_with_length(0))

        # Initialize the array of instance invokables
        system_class.set_instance_invokables(self.new_array_with_length(0))
        system_class.get_class(self).set_instance_invokables(self.new_array_with_length(0))

        # Initialize the name of the system class
        system_class.set_name(self.symbol_for(name))
        system_class.get_class(self).set_name(self.symbol_for(name + " class"))

        # Insert the system class into the dictionary of globals
        self.set_global(system_class.get_name(), system_class)

    def get_global(self, name):
        # Return the global with the given name if it's in the dictionary of globals
        # if not, return None
        jit.promote(self)
        assoc = self._get_global(name)
        if assoc:
            return assoc.get_value()
        else:
            return None

    @jit.elidable
    def _get_global(self, name):
        return self._globals.get(name, None)

    def set_global(self, name, value):
        self.get_globals_association(name).set_value(value)

    @jit.elidable_promote("all")
    def has_global(self, name):
        return name in self._globals

    @jit.elidable_promote("all")
    def get_globals_association(self, name):
        assoc = self._globals.get(name, None)
        if assoc is None:
            assoc = Assoc(name, nilObject)
            self._globals[name] = assoc
        return assoc

    def _get_block_class(self, number_of_arguments):
        return self.blockClasses[number_of_arguments]

    def _make_block_class(self, number_of_arguments):
        # Compute the name of the block class with the given number of
        # arguments
        name = self.symbol_for("Block" + str(number_of_arguments))

        # Get the block class for blocks with the given number of arguments
        result = self._load_class(name, None)

        # Add the appropriate value primitive to the block class
        result.add_instance_primitive(
            block_evaluation_primitive(number_of_arguments, self), True)

        # Insert the block class into the dictionary of globals
        self.set_global(name, result)

        # Return the loaded block class
        return result

    def load_class(self, name):
        # Check if the requested class is already in the dictionary of globals
        result = self.get_global(name)
        if result is not None:
            return result

        # Load the class
        result = self._load_class(name, None)
        self._load_primitives(result, False)
        self.set_global(name, result)
        return result

    @staticmethod
    def _load_primitives(clazz, is_system_class):
        if not clazz: return

        if clazz.has_primitives() or is_system_class:
            clazz.load_primitives(not is_system_class)

    def _load_system_class(self, system_class):
        # Load the system class
        result = self._load_class(system_class.get_name(), system_class)

        if not result:
            error_println(system_class.get_name().get_embedded_string()
                   + " class could not be loaded. It is likely that the"
                   + " class path has not been initialized properly."
                   + " Please make sure that the '-cp' parameter is given on the command-line.")
            self.exit(200)

        self._load_primitives(result, True)

    def _load_class(self, name, system_class):
        # Try loading the class from all different paths
        for cpEntry in self.classpath:
            try:
                # Load the class from a file and return the loaded class
                result = sourcecode_compiler.compile_class_from_file(
                    cpEntry, name.get_embedded_string(), system_class, self)
                if self._dump_bytecodes:
                    from som.compiler.disassembler import dump
                    dump(result.get_class(self))
                    dump(result)

                return result
            except IOError:
                # Continue trying different paths
                pass

        # The class could not be found.
        return None

    def load_shell_class(self, stmt):
        # Load the class from a stream and return the loaded class
        result = sourcecode_compiler.compile_class_from_string(stmt, None, self)
        if self._dump_bytecodes:
            from som.compiler.disassembler import dump
            dump(result)
        return result


class _ASTUniverse(Universe):

    def _start_shell(self):
        shell = AstShell(self)
        return shell.start()

    def _start_execution(self, system_object, initialize, arguments_array):
        return initialize.invoke(system_object, [arguments_array])

    def _start_method_execution(self, clazz, invokable):
        return invokable.invoke(clazz, [])


class _BCUniverse(Universe):

    def __init__(self, avoid_exit = False):
        self._interpreter = Interpreter(self)
        Universe.__init__(self, avoid_exit)

    def get_interpreter(self):
        return self._interpreter

    def _start_shell(self):
        bootstrap_method = create_bootstrap_method(self)
        shell = BcShell(self, self._interpreter, bootstrap_method)
        return shell.start()

    def _start_execution(self, system_object, initialize, arguments_array):
        bootstrap_method = create_bootstrap_method(self)
        bootstrap_frame = create_bootstrap_frame(bootstrap_method, system_object, arguments_array)
        # Lookup the initialize invokable on the system class
        return initialize.invoke(bootstrap_frame, self._interpreter)

    def _start_method_execution(self, clazz, invokable):
        bootstrap_method = create_bootstrap_method(self)
        bootstrap_frame = create_bootstrap_frame(bootstrap_method, clazz)

        invokable.invoke(bootstrap_frame, self._interpreter)
        return bootstrap_frame.pop()

    def _initialize_object_system(self):
        system_object = Universe._initialize_object_system(self)
        self._interpreter.initialize_known_quick_sends()
        return system_object


def create_universe(avoid_exit = False):
    if is_ast_interpreter():
        return _ASTUniverse(avoid_exit)
    else:
        return _BCUniverse(avoid_exit)


_current = create_universe()


def set_current(universe):
    global _current
    _current = universe


def error_print(msg):
    os.write(2, encode_to_bytes(msg or ""))


def error_println(msg = b""):
    os.write(2, encode_to_bytes(msg + "\n"))


def std_print(msg):
    os.write(1, encode_to_bytes(msg or ""))


def std_println(msg = ""):
    os.write(1, encode_to_bytes(msg + "\n"))


def main(args):
    jit.set_param(None, 'trace_limit', 15000)
    u = _current
    u.interpret(args[1:])
    u.exit(0)


def get_current():
    return _current


if __name__ == '__main__':
    raise RuntimeError("Universe should not be used as main anymore")
