import os
import time

from rlib import jit
from rlib.string_stream import encode_to_bytes
from rlib.exit import Exit
from rlib.osext import path_split
from rlib import rgc
from som.vm.symbols import symbol_for, sym_false, sym_true, sym_nil

from som.vmobjects.array import Array
from som.vmobjects.block_bc import block_evaluation_primitive
from som.vmobjects.clazz import Class
from som.vmobjects.object_without_fields import ObjectWithoutFields
from som.vmobjects.object_with_layout import Object
from som.vmobjects.string import String

from som.vm.globals import nilObject, trueObject, falseObject
from som.vm.shell import Shell

from som.compiler.sourcecode_compiler import (
    compile_class_from_file,
    compile_class_from_string,
)


class Assoc(object):
    _immutable_fields_ = ["global_name", "value?"]

    def __init__(self, global_name, value):
        self.global_name = global_name
        self.value = value

    def __str__(self):
        return "(%s => %s)" % (self.global_name, self.value)


class Universe(object):
    _immutable_fields_ = [
        "object_class",
        "class_class",
        "metaclass_class",
        "nil_class",
        "integer_class",
        "integer_layout?",
        "array_class",
        "array_layout?",
        "method_class",
        "method_layout?",
        "symbol_class",
        "symbol_layout?",
        "primitive_class",
        "primitive_layout?",
        "system_class",
        "block_class",
        "block_classes[*]",
        "block_layouts?[*]",
        "string_class",
        "string_layout?",
        "double_class",
        "double_layout?",
        "_globals",
        "start_time",
        "_object_system_initialized",
    ]

    def __init__(self, avoid_exit=False):
        self._globals = {}

        self.object_class = None
        self.class_class = None
        self.metaclass_class = None

        self.nil_class = None
        self.integer_class = None
        self.integer_layout = None
        self.array_class = None
        self.array_layout = None
        self.method_class = None
        self.method_layout = None
        self.symbol_class = None
        self.symbol_layout = None
        self.primitive_class = None
        self.primitive_layout = None
        self.system_class = None
        self.block_class = None
        self.block_classes = None
        self.block_layouts = None
        self.string_class = None
        self.string_layout = None
        self.double_class = None
        self.double_layout = None

        self._last_exit_code = 0
        self._avoid_exit = avoid_exit
        self._dump_bytecodes = False
        self.classpath = None
        self.start_time = time.time()  # a float of the time in seconds
        self._object_system_initialized = False

    def reset(self, avoid_exit):
        self.__init__(avoid_exit)  # pylint: disable=unnecessary-dunder-call

    def exit(self, error_code):
        if self._avoid_exit:
            self._last_exit_code = error_code
        else:
            raise Exit(error_code)

    def last_exit_code(self):
        return self._last_exit_code

    def execute_method(self, class_name, selector):
        self._initialize_object_system()

        clazz = self.load_class(symbol_for(class_name))
        if clazz is None:
            raise Exception("Class " + class_name + " could not be loaded.")

        # Lookup the invokable on class
        invokable = clazz.get_class(self).lookup_invokable(symbol_for(selector))
        if invokable is None:
            raise Exception("Lookup of " + selector + " failed in class " + class_name)

        return invokable.invoke_1(clazz)

    def interpret(self, arguments):
        # Check for command line switches
        arguments = self.handle_arguments(arguments)

        # Initialize the known universe
        system_object = self._initialize_object_system()

        # Start the shell if no filename is given
        if len(arguments) == 0:
            shell = Shell(self)
            return shell.start()
        arguments_array = self.new_array_with_strings(arguments)
        initialize = self.system_class.lookup_invokable(symbol_for("initialize:"))
        return initialize.invoke_2(system_object, arguments_array)

    def handle_arguments(self, arguments):
        got_classpath = False
        remaining_args = []
        saw_others = False

        i = 0
        while i < len(arguments):
            if arguments[i] == "-cp" and not saw_others:
                if i + 1 >= len(arguments):
                    self._print_usage_and_exit()
                self.setup_classpath(arguments[i + 1])
                i += 1  # skip class path
                got_classpath = True
            elif arguments[i] == "-d" and not saw_others:
                self._dump_bytecodes = True
            elif arguments[i] in ["-h", "--help", "-?"] and not saw_others:
                self._print_usage_and_exit()
            elif arguments[i] == "--no-gc" and not saw_others:
                rgc.disable()
                if rgc.isenabled() == 0:
                    print("GC successfully disabled.")
                else:
                    print("GC still enabled.")
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

    def setup_classpath(self, class_path):
        self.classpath = class_path.split(os.pathsep)

    @staticmethod
    def _default_classpath():
        return ["."]

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
        std_println("    -cp <directories separated by " + os.pathsep + ">")
        std_println("        set search path for application classes")
        std_println("    -d  enable disassembling")
        std_println("    -h  print this help")
        std_println("")
        std_println("    --no-gc disable garbage collection")

        # Exit
        self.exit(0)

    def _initialize_object_system(self):
        # Allocate the Metaclass classes
        self.metaclass_class = self.new_metaclass_class()

        # Allocate the rest of the system classes
        self.object_class = self.new_system_class()
        self.nil_class = self.new_system_class()
        self.class_class = self.new_system_class()

        self.array_class = self.new_system_class()
        self.array_layout = self.array_class.get_layout_for_instances()

        self.symbol_class = self.new_system_class()
        self.symbol_layout = self.symbol_class.get_layout_for_instances()

        self.method_class = self.new_system_class()
        self.method_layout = self.method_class.get_layout_for_instances()

        self.integer_class = self.new_system_class()
        self.integer_layout = self.integer_class.get_layout_for_instances()

        self.primitive_class = self.new_system_class()
        self.primitive_layout = self.primitive_class.get_layout_for_instances()

        self.string_class = self.new_system_class()
        self.string_layout = self.string_class.get_layout_for_instances()

        self.double_class = self.new_system_class()
        self.double_layout = self.double_class.get_layout_for_instances()

        # Setup the class reference for the nil object
        nilObject.set_class(self.nil_class)

        # Initialize the system classes
        self._initialize_system_class(self.object_class, None, "Object")
        self._initialize_system_class(self.class_class, self.object_class, "Class")
        self._initialize_system_class(
            self.metaclass_class, self.class_class, "Metaclass"
        )
        self._initialize_system_class(self.nil_class, self.object_class, "Nil")
        self._initialize_system_class(self.array_class, self.object_class, "Array")
        self._initialize_system_class(self.method_class, self.object_class, "Method")
        self._initialize_system_class(self.integer_class, self.object_class, "Integer")
        self._initialize_system_class(
            self.primitive_class, self.object_class, "Primitive"
        )
        self._initialize_system_class(self.string_class, self.object_class, "String")
        self._initialize_system_class(self.symbol_class, self.string_class, "Symbol")
        self._initialize_system_class(self.double_class, self.object_class, "Double")

        # Load methods and fields into the system classes
        self._load_system_class(self.object_class)
        self._load_system_class(self.class_class)
        self._load_system_class(self.metaclass_class)
        self._load_system_class(self.nil_class)
        self._load_system_class(self.array_class)
        self._load_system_class(self.method_class)
        self._load_system_class(self.string_class)
        self._load_system_class(self.symbol_class)
        self._load_system_class(self.integer_class)
        self._load_system_class(self.primitive_class)
        self._load_system_class(self.double_class)

        # Load the generic block class
        self.block_class = self.load_class(symbol_for("Block"))

        # Setup the true and false objects
        true_class_name = symbol_for("True")
        true_class = self.load_class(true_class_name)
        true_class.load_primitives(False, self)
        trueObject.set_class(true_class)

        false_class_name = symbol_for("False")
        false_class = self.load_class(false_class_name)
        false_class.load_primitives(False, self)
        falseObject.set_class(false_class)

        # Load the system class and create an instance of it
        self.system_class = self.load_class(symbol_for("System"))
        system_object = self.new_instance(self.system_class)

        # Put special objects and classes into the dictionary of globals
        self.set_global(sym_nil, nilObject)
        self.set_global(sym_true, trueObject)
        self.set_global(sym_false, falseObject)
        self.set_global(symbol_for("system"), system_object)
        self.set_global(symbol_for("System"), self.system_class)
        self.set_global(symbol_for("Block"), self.block_class)

        self.set_global(symbol_for("Nil"), self.nil_class)

        self.set_global(true_class_name, true_class)
        self.set_global(false_class_name, false_class)

        self.block_classes = [self.block_class] + [
            self._make_block_class(i) for i in [1, 2, 3]
        ]

        self.block_layouts = [c.get_layout_for_instances() for c in self.block_classes]

        self._object_system_initialized = True
        return system_object

    def is_object_system_initialized(self):
        return self._object_system_initialized

    @staticmethod
    def new_array_with_strings(strings):
        values = [String(s) for s in strings]
        return Array.from_objects(values)

    @staticmethod
    def new_instance(instance_class):
        layout = instance_class.get_layout_for_instances()
        num_fields = layout.get_number_of_fields()
        if num_fields == 0:
            return ObjectWithoutFields(layout)
        return Object(layout)

    def new_metaclass_class(self):
        # Allocate the metaclass classes
        class_class = Class(0, None)
        result = Class(0, class_class)

        # Setup the metaclass hierarchy
        result.get_class(self).set_class(result)
        return result

    def new_system_class(self):
        # Allocate the new system class
        system_class_class = Class(0, None)
        system_class = Class(0, system_class_class)

        # Setup the metaclass hierarchy
        system_class.get_class(self).set_class(self.metaclass_class)
        return system_class

    def _initialize_system_class(self, system_class, super_class, name):
        # Initialize the superclass hierarchy
        if super_class:
            system_class.set_super_class(super_class)
            system_class.get_class(self).set_super_class(super_class.get_class(self))
        else:
            system_class.get_class(self).set_super_class(self.class_class)

        # Initialize the array of instance fields
        system_class.set_instance_fields(Array.from_size(0))
        system_class.get_class(self).set_instance_fields(Array.from_size(0))

        # Initialize the name of the system class
        system_class.set_name(symbol_for(name))
        system_class.get_class(self).set_name(symbol_for(name + " class"))

        # Insert the system class into the dictionary of globals
        self.set_global(system_class.get_name(), system_class)

    def get_global(self, name):
        # Return the global with the given name if it's in the dictionary of globals
        # if not, return None
        jit.promote(self)
        assoc = self._get_global(name)
        if assoc:
            return assoc.value
        return None

    @jit.elidable
    def _get_global(self, name):
        return self._globals.get(name, None)

    def set_global(self, name, value):
        self.get_globals_association(name).value = value

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

    def get_globals_association_or_none(self, name):
        return self._globals.get(name, None)

    def _make_block_class(self, number_of_arguments):
        # Compute the name of the block class with the given number of
        # arguments
        name = symbol_for("Block" + str(number_of_arguments))

        # Get the block class for blocks with the given number of arguments
        result = self._load_class(name, None)

        # Add the appropriate value primitive to the block class
        result.add_primitive(block_evaluation_primitive(number_of_arguments), True)

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

    def _load_primitives(self, clazz, is_system_class):
        if not clazz:
            return

        if clazz.needs_primitives() or is_system_class:
            clazz.load_primitives(not is_system_class, self)

    def _load_system_class(self, system_class):
        # Load the system class
        result = self._load_class(system_class.get_name(), system_class)

        if not result:
            error_println(
                system_class.get_name().get_embedded_string()
                + " class could not be loaded. It is likely that the"
                + " class path has not been initialized properly."
                + " Please make sure that the '-cp' parameter is given on the command-line."
            )
            self.exit(200)

        self._load_primitives(result, True)

    def _load_class(self, name, system_class):
        # Try loading the class from all different paths
        for cp_entry in self.classpath:
            try:
                # Load the class from a file and return the loaded class
                result = compile_class_from_file(
                    cp_entry, name.get_embedded_string(), system_class, self
                )
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
        result = compile_class_from_string(stmt, None, self)
        if self._dump_bytecodes:
            from som.compiler.disassembler import dump

            dump(result)
        return result


def create_universe(avoid_exit=False):
    return Universe(avoid_exit)


def error_print(msg):
    os.write(2, encode_to_bytes(msg or ""))


def error_println(msg=""):
    os.write(2, encode_to_bytes(msg + "\n"))


def std_print(msg):
    os.write(1, encode_to_bytes(msg or ""))


def std_println(msg=""):
    os.write(1, encode_to_bytes(msg + "\n"))


def main(args):
    jit.set_param(None, "trace_limit", 15000)
    from som.vm.current import current_universe

    u = current_universe
    u.interpret(args[1:])
    u.exit(0)


if __name__ == "__main__":
    raise RuntimeError("Universe should not be used as main anymore")
