from som.interpreter.interpreter import Interpreter
from som.interpreter.bytecodes   import Bytecodes 
from som.vm.symbol_table         import SymbolTable
from som.vmobjects.object        import Object
from som.vmobjects.clazz         import Class
from som.vmobjects.array         import Array
from som.vmobjects.symbol        import Symbol
from som.vmobjects.method        import Method
from som.vmobjects.integer       import Integer
from som.vmobjects.string        import String
from som.vmobjects.block         import Block, block_evaluation_primitive
from som.vmobjects.frame         import Frame
from som.vmobjects.biginteger    import BigInteger
from som.vmobjects.double        import Double

from som.vm.shell import Shell

import som.compiler.sourcecode_compiler as sourcecode_compiler

import os

class Exit(BaseException):
    def __init__(self, code):
        self.code = code

class Universe(object):
    
    def __init__(self, avoid_exit = False):
        self._interpreter    = Interpreter(self)
        self._symbol_table   = SymbolTable()
        
        self._globals        = {}
        
        self.nilObject      = None
        self.trueObject     = None
        self.falseObject    = None
        self.objectClass    = None
        self.classClass     = None
        self.metaclassClass = None
        
        self.nilClass       = None
        self.integerClass   = None
        self.bigintegerClass= None
        self.arrayClass     = None
        self.methodClass    = None
        self.symbolClass    = None
        self.frameClass     = None
        self.primitiveClass = None
        self.systemClass    = None
        self.blockClass     = None
        self.stringClass    = None
        self.doubleClass    = None
        
        self._last_exit_code = 0
        self._avoid_exit     = avoid_exit
        self._dump_bytecodes = False
        self.classpath      = None

    def exit(self, error_code):
        if self._avoid_exit:
            self._last_exit_code = error_code
        else:
            raise Exit(error_code)
    
    def last_exit_code(self):
        return self._last_exit_code
    
    def get_interpreter(self):
        return self._interpreter
    
    def execute_method(self, class_name, selector):
        self._initialize_object_system()

        clazz = self.load_class(self.symbol_for(class_name))

        # Lookup the invokable on class
        invokable = clazz.get_class().lookup_invokable(self.symbol_for(selector))

        bootstrap_method = self._create_bootstrap_method()
        bootstrap_frame  = self._create_bootstrap_frame(bootstrap_method, clazz)
        
        return self.start(bootstrap_frame, invokable)
    
    def _create_bootstrap_method(self):
        # Create a fake bootstrap method to simplify later frame traversal
        bootstrap_method = self.new_method(self.symbol_for("bootstrap"), 1, 0)
        bootstrap_method.set_bytecode(0, Bytecodes.halt)
        bootstrap_method.set_number_of_locals(self.new_integer(0))
        bootstrap_method.set_maximum_number_of_stack_elements(self.new_integer(2))
        bootstrap_method.set_holder(self.systemClass)
        return bootstrap_method
    
    def _create_bootstrap_frame(self, bootstrap_method, receiver, arguments = None):
        # Create a fake bootstrap frame with the system object on the stack
        bootstrap_frame = self._interpreter.push_new_frame(bootstrap_method)
        bootstrap_frame.push(receiver)
        
        if arguments:
            bootstrap_frame.push(arguments)
        return bootstrap_frame
        
    
    def interpret(self, arguments):
        # Check for command line switches
        arguments = self.handle_arguments(arguments)

        # Initialize the known universe
        system_object = self._initialize_object_system()
        bootstrap_method = self._create_bootstrap_method()
        
        # Start the shell if no filename is given
        if len(arguments) == 0:
            shell = Shell(self, self._interpreter)
            shell.set_bootstrap_method(bootstrap_method)
            shell.start()
            return
        else:
            # Convert the arguments into an array
            arguments_array = self.new_array_with_strings(arguments)
            bootstrap_frame = self._create_bootstrap_frame(bootstrap_method, system_object, arguments_array)
            # Lookup the initialize invokable on the system class
            initialize = self.systemClass.lookup_invokable(self.symbol_for("initialize:"))

            self.start(bootstrap_frame, initialize)
    
    def start(self, bootstrap_frame, invokable):
        # Invoke the initialize invokable
        invokable.invoke(bootstrap_frame, self._interpreter)

        # Start the interpreter
        return self._interpreter.start()
    
    def handle_arguments(self, arguments):
        got_classpath  = False
        remaining_args = []

        i = 0
        while i < len(arguments):
            if arguments[i] == "-cp":
                if i + 1 >= len(arguments):
                    self._print_usage_and_exit()
                self.setup_classpath(arguments[i + 1])
                i += 1    # skip class path
                got_classpath = True
            elif arguments[i] == "-d":
                self._dump_bytecodes = True
            else:
                remaining_args.append(arguments[i])
            i += 1
    
        if not got_classpath:
            # Get the default class path of the appropriate size
            self.classpath = self._setup_default_classpath()

        # check remaining args for class paths, and strip file extension
        i = 0
        while i < len(remaining_args):
            split = self._get_path_class_ext(remaining_args[i])

            if split[0] != "":  # there was a path
                self.classpath.insert(0, split[0])
        
            remaining_args[i] = split[1]
            i += 1
        
        return remaining_args
    
    def setup_classpath(self, cp):
        self.classpath = cp.split(os.pathsep)
    
    def _setup_default_classpath(self):
        return ['.']
    
    # take argument of the form "../foo/Test.som" and return
    # "../foo", "Test", "som"
    def _get_path_class_ext(self, path):
        path_and_file = path.rsplit(os.pathsep, 1)
        if len(path_and_file) <= 1:
            path = ""
        else:
            path = path_and_file[0]
        file_and_ext  = path_and_file[-1].rsplit(".", 1)
        if len(file_and_ext) <= 1:
            ext = ""
        else:
            ext = file_and_ext[-1]
        file_name = file_and_ext[0]
        return (path, file_name, ext)
    
    def _print_usage_and_exit(self):
        # Print the usage
        std_println("Usage: som [-options] [args...]                          ")
        std_println("                                                         ")
        std_println("where options include:                                   ")
        std_println("    -cp <directories separated by " + os.pathsep     + ">")
        std_println("                  set search path for application classes")
        std_println("    -d            enable disassembling")

        # Exit
        self.exit(0)

    def _initialize_object_system(self):
        # Allocate the nil object
        self.nilObject = Object(None)

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
        self.bigintegerClass = self.new_system_class()
        self.frameClass      = self.new_system_class()
        self.primitiveClass  = self.new_system_class()
        self.stringClass     = self.new_system_class()
        self.doubleClass     = self.new_system_class()

        # Setup the class reference for the nil object
        self.nilObject.set_class(self.nilClass)

        # Initialize the system classes
        self._initialize_system_class(self.objectClass,                 None, "Object")
        self._initialize_system_class(self.classClass,      self.objectClass, "Class")
        self._initialize_system_class(self.metaclassClass,   self.classClass, "Metaclass")
        self._initialize_system_class(self.nilClass,        self.objectClass, "Nil")
        self._initialize_system_class(self.arrayClass,      self.objectClass, "Array")
        self._initialize_system_class(self.methodClass,      self.arrayClass, "Method")
        self._initialize_system_class(self.symbolClass,     self.objectClass, "Symbol")
        self._initialize_system_class(self.integerClass,    self.objectClass, "Integer")
        self._initialize_system_class(self.bigintegerClass, self.objectClass, "BigInteger")
        self._initialize_system_class(self.frameClass,       self.arrayClass, "Frame")
        self._initialize_system_class(self.primitiveClass,  self.objectClass, "Primitive")
        self._initialize_system_class(self.stringClass,     self.objectClass, "String")
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
        self._load_system_class(self.bigintegerClass)
        self._load_system_class(self.frameClass)
        self._load_system_class(self.primitiveClass)
        self._load_system_class(self.stringClass)
        self._load_system_class(self.doubleClass)

        # Load the generic block class
        self.blockClass = self.load_class(self.symbol_for("Block"))

        # Setup the true and false objects
        self.trueObject  = self.new_instance(self.load_class(self.symbol_for("True")))
        self.falseObject = self.new_instance(self.load_class(self.symbol_for("False")))

        # Load the system class and create an instance of it
        self.systemClass = self.load_class(self.symbol_for("System"))
        system_object = self.new_instance(self.systemClass)

        # Put special objects and classes into the dictionary of globals
        self.set_global(self.symbol_for("nil"),    self.nilObject)
        self.set_global(self.symbol_for("true"),   self.trueObject)
        self.set_global(self.symbol_for("false"),  self.falseObject)
        self.set_global(self.symbol_for("system"), system_object)
        self.set_global(self.symbol_for("System"), self.systemClass)
        self.set_global(self.symbol_for("Block"),  self.blockClass)
        return system_object
    
    def symbol_for(self, string):
        # Lookup the symbol in the symbol table
        result = self._symbol_table.lookup(string)
        if result:
            return result
        
        # Create a new symbol and return it
        result = self.new_symbol(string)
        return result
    
    def new_array_with_length(self, length):
        # Allocate a new array and set its class to be the array class
        result = Array(self.nilObject)
        result.set_class(self.arrayClass)

        # Set the number of indexable fields to the given value (length)
        result.set_number_of_indexable_fields_and_clear(length, self.nilObject)

        # Return the freshly allocated array
        return result
  
    def new_array_from_list(self, values):
        # Allocate a new array with the same length as the list
        result = self.new_array_with_length(len(values))

        # Copy all elements from the list into the array
        for i in range(len(values)):
            result.set_indexable_field(i, values[i])
    
        # Return the allocated and initialized array
        return result
  
    def new_array_with_strings(self, strings):
        # Allocate a new array with the same length as the string array
        result = self.new_array_with_length(len(strings))

        # Copy all elements from the string array into the array
        for i in range(len(strings)):
            result.set_indexable_field(i, self.new_string(strings[i]))
    
        # Return the allocated and initialized array
        return result
    
    def new_block(self, method, context_frame, arguments):
        # Allocate a new block and set its class to be the block class
        result = Block(self.nilObject)
        result.set_class(self._get_block_class(arguments))

        # Set the method and context of block
        result.set_method(method)
        result.set_context(context_frame)

        # Return the freshly allocated block
        return result

    def new_class(self, class_class):
        # Allocate a new class and set its class to be the given class class
        result = Class(self, class_class.get_number_of_instance_fields())
        result.set_class(class_class)

        # Return the freshly allocated class
        return result

    def new_frame(self, previous_frame, method):
        # Allocate a new frame and set its class to be the frame class
        result = Frame(self.nilObject)
        result.set_class(self.frameClass)

        # Compute the maximum number of stack locations (including arguments,
        # locals and extra buffer to support doesNotUnderstand) and set the
        # number of indexable fields accordingly
        length = (method.get_number_of_arguments() +
                  method.get_number_of_locals().get_embedded_integer() +
                  method.get_maximum_number_of_stack_elements().get_embedded_integer() + 2)
        result.set_number_of_indexable_fields_and_clear(length, self.nilObject)

        # Set the method of the frame and the previous frame
        result.set_method(method)
        if previous_frame:
            result.set_previous_frame(previous_frame)

        # Reset the stack pointer and the bytecode index
        result.reset_stack_pointer()
        result.set_bytecode_index(0)

        # Return the freshly allocated frame
        return result

    def new_method(self, signature, num_bytecodes, num_literals):
        # Allocate a new method and set its class to be the method class
        result = Method(self.nilObject)
        result.set_class(self.methodClass)

        # Set the signature and the number of bytecodes
        result.set_signature(signature)
        result.set_number_of_bytecodes(num_bytecodes)
        result.set_number_of_indexable_fields_and_clear(num_literals, self.nilObject)

        # Return the freshly allocated method
        return result

    def new_instance(self, instance_class):
        # Allocate a new instance and set its class to be the given class
        result = Object(self.nilObject, instance_class.get_number_of_instance_fields())
        result.set_class(instance_class)
 
        # Return the freshly allocated instance
        return result

 
    def new_integer(self, value):
        # Allocate a new integer and set its class to be the integer class
        result = Integer(self.nilObject)
        result.set_class(self.integerClass)
     
        # Set the embedded integer of the newly allocated integer
        result.set_embedded_integer(value)
     
        # Return the freshly allocated integer
        return result
 
    def new_biginteger(self, value):
        # Allocate a new integer and set its class to be the integer class
        result = BigInteger(self.nilObject)
        result.set_class(self.bigintegerClass)
 
        # Set the embedded integer of the newly allocated integer
        result.set_embedded_biginteger(value)
 
        # Return the freshly allocated integer
        return result
 
 
    def new_double(self, value):
        # Allocate a new integer and set its class to be the double class
        result = Double(self.nilObject)
        result.set_class(self.doubleClass)
 
        # Set the embedded double of the newly allocated double
        result.set_embedded_double(value)
 
        # Return the freshly allocated double
        return result
    
    def new_metaclass_class(self):
        # Allocate the metaclass classes
        result = Class(self)
        result.set_class(Class(self))

        # Setup the metaclass hierarchy
        result.get_class().set_class(result)

        # Return the freshly allocated metaclass class
        return result

    def new_string(self, embedded_string):
        # Allocate a new string and set its class to be the string class
        result = String(self.nilObject)
        result.set_class(self.stringClass)
 
        # Put the embedded string into the new string
        result.set_embedded_string(embedded_string)
 
        # Return the freshly allocated string
        return result
    
    def new_symbol(self, string):
        # Allocate a new symbol and set its class to be the symbol class
        result = Symbol(self.nilObject)
        result.set_class(self.symbolClass)

        # Put the string into the symbol
        result.set_string(string)

        # Insert the new symbol into the symbol table
        self._symbol_table.insert(result)

        # Return the freshly allocated symbol
        return result
      
    def new_system_class(self):
        # Allocate the new system class
        system_class = Class(self)

        # Setup the metaclass hierarchy
        system_class.set_class(Class(self))
        system_class.get_class().set_class(self.metaclassClass)

        # Return the freshly allocated system class
        return system_class
    
    def _initialize_system_class(self, system_class, super_class, name):
        # Initialize the superclass hierarchy
        if super_class:
            system_class.set_super_class(super_class)
            system_class.get_class().set_super_class(super_class.get_class())
        else:
            system_class.get_class().set_super_class(self.classClass)
    

        # Initialize the array of instance fields
        system_class.set_instance_fields(self.new_array_with_length(0))
        system_class.get_class().set_instance_fields(self.new_array_with_length(0))

        # Initialize the array of instance invokables
        system_class.set_instance_invokables(self.new_array_with_length(0))
        system_class.get_class().set_instance_invokables(self.new_array_with_length(0))

        # Initialize the name of the system class
        system_class.set_name(self.symbol_for(name))
        system_class.get_class().set_name(self.symbol_for(name + " class"))

        # Insert the system class into the dictionary of globals
        self.set_global(system_class.get_name(), system_class)
    
    
    def get_global(self, name):
        # Return the global with the given name if it's in the dictionary of globals
        if self.has_global(name):
            return self._globals[name]

        # Global not found
        return None

    def set_global(self, name, value):
        # Insert the given value into the dictionary of globals
        self._globals[name] = value
  

    def has_global(self, name):
        # Returns if the universe has a value for the global of the given name
        return name in self._globals
    
    def _get_block_class(self, number_of_arguments = None):
        if not number_of_arguments:
            # Get the generic block class
            return self.blockClass
        
        # Compute the name of the block class with the given number of
        # arguments
        name = self.symbol_for("Block" + str(number_of_arguments))

        # Lookup the specific block class in the dictionary of globals and
        # return it
        if self.has_global(name):
            return self.get_global(name)

        # Get the block class for blocks with the given number of arguments
        result = self._load_class(name, None)

        # Add the appropriate value primitive to the block class
        result.add_instance_primitive(block_evaluation_primitive(number_of_arguments, self))

        # Insert the block class into the dictionary of globals
        self.set_global(name, result)

        # Return the loaded block class
        return result

    def load_class(self, name):
        # Check if the requested class is already in the dictionary of globals
        if self.has_global(name):
            return self.get_global(name)

        # Load the class
        result = self._load_class(name, None)

        # Load primitives (if necessary) and return the resulting class
        if result and result.has_primitives():
            result.load_primitives()
    
        return result

    def _load_system_class(self, system_class):
        # Load the system class
        result = self._load_class(system_class.get_name(), system_class)

        # Load primitives if necessary
        if result.has_primitives():
            result.load_primitives()

    def _load_class(self, name, system_class):
        # Try loading the class from all different paths
        for cpEntry in self.classpath:
            try:
                # Load the class from a file and return the loaded class
                result = sourcecode_compiler.compile_class_from_file(cpEntry, name.get_string(), system_class, self)
                if self._dump_bytecodes:
                    from som.compiler.disassembler import dump
                    dump(result.get_class())
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

def error_print(msg):
    os.write(2, msg)

def error_println(msg = ""):
    os.write(2, msg + "\n")

def std_print(msg):
    print msg,

def std_println(msg=""):
    print msg


def main(args):
    u = Universe()
    u.interpret(args[1:])
    u.exit(0)

if __name__ == '__main__':
    import sys
    try:
        main(sys.argv)
    except Exit as e:
        sys.exit(e.code)
