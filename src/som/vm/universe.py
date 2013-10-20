from __future__ import print_function

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
from som.vmobjects.block         import Block
from som.vmobjects.frame         import Frame
from som.vmobjects.biginteger    import BigInteger
from som.vmobjects.double        import Double

from som.vm.shell import Shell

import som.compiler.sourcecode_compiler as sourcecode_compiler

import os
import sys

class Universe(object):
    
    def __init__(self, avoid_exit = False):
        self._interpreter    = Interpreter(self)
        self._symbol_table   = SymbolTable()
        
        self._globals        = {}
        
        self._nilObject      = None
        self._trueObject     = None
        self._falseObject    = None
        self._objectClass    = None
        self._classClass     = None
        self._metaclassClass = None
        
        self._nilClass       = None
        self._integerClass   = None
        self._bigintegerClass= None
        self._arrayClass     = None
        self._methodClass    = None
        self._symbolClass    = None
        self._frameClass     = None
        self._primitiveClass = None
        self._systemClass    = None
        self._blockClass     = None
        self._stringClass    = None
        self._doubleClass    = None
        
        self._last_exit_code = 0
        self._avoid_exit     = avoid_exit
        self._classpath      = None
        self._dump_bytecodes = False        
    
    @property
    def nilObject(self):
        return self._nilObject
    
    @property
    def trueObject(self):
        return self._trueObject
    
    @property
    def falseObject(self):
        return self._falseObject
    
    @property
    def objectClass(self):
        return self._objectClass
    
    @property
    def classClass(self):
        return self._classClass
    
    @property
    def nilClass(self):
        return self._nilClass
    
    @property
    def integerClass(self):
        return self._integerClass
    
    @property
    def bigintegerClass(self):
        return self._bigintegerClass

    @property
    def arrayClass(self):
        return self._arrayClass
    
    @property
    def methodClass(self):
        return self._methodClass
    
    @property
    def symbolClass(self):
        return self._symbolClass
    
    @property
    def frameClass(self):
        return self._frameClass
    
    @property
    def systemClass(self):
        return self._systemClass
    
    @property
    def blockClass(self):
        return self._blockClass
    
    @property
    def stringClass(self):
        return self._stringClass
    
    @property
    def doubleClass(self):
        return self._doubleClass
    
    @property
    def primitiveClass(self):
        return self._primitiveClass
    
    @property
    def metaclassClass(self):
        return self._metaclassClass
    
    def exit(self, error_code):
        if self._avoid_exit:
            self._last_exit_code = error_code
        else:
            sys.exit(error_code)
    
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
        bootstrap_method = self.new_method(self.symbol_for("bootstrap"), 1, 0,
                                           self.new_integer(0),
                                           self.new_integer(2))
        bootstrap_method.set_bytecode(0, Bytecodes.halt)
        bootstrap_method.set_holder(self._systemClass)
        return bootstrap_method
    
    def _create_bootstrap_frame(self, bootstrap_method, receiver, arguments = None):
        # Create a fake bootstrap frame with the system object on the stack
        bootstrap_frame = self._interpreter.push_new_frame(bootstrap_method, self._nilObject)
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
            initialize = self._systemClass.lookup_invokable(self.symbol_for("initialize:"))

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
            elif arguments[i] in ["-h", "--help", "-?"]:
                self._print_usage_and_exit()
            else:
                remaining_args.append(arguments[i])
            i += 1
    
        if not got_classpath:
            # Get the default class path of the appropriate size
            self._classpath = self._setup_default_classpath()

        # check remaining args for class paths, and strip file extension
        i = 0
        while i < len(remaining_args):
            split = self._get_path_class_ext(remaining_args[i])

            if split[0] != "":  # there was a path
                self._classpath.insert(0, split[0])
        
            remaining_args[i] = split[1]
            i += 1
        
        return remaining_args
    
    def setup_classpath(self, cp):
        self._classpath = cp.split(os.pathsep)
    
    def _setup_default_classpath(self):
        return ['.']
    
    # take argument of the form "../foo/Test.som" and return
    # "../foo", "Test", "som"
    def _get_path_class_ext(self, path):
        (path, file_name) = os.path.split(path)
        (file_name, ext)  = os.path.splitext(file_name)
        return (path, file_name, ext[1:])
    
    def _print_usage_and_exit(self):
        # Print the usage
        self.std_println("Usage: som [-options] [args...]                          ")
        self.std_println("                                                         ")
        self.std_println("where options include:                                   ")
        self.std_println("    -cp <directories separated by " + os.pathsep     + ">")
        self.std_println("                  set search path for application classes")
        self.std_println("    -d            enable disassembling")
        self.std_println("    -h  print this help")

        # Exit
        self.exit(0)

    def _initialize_object_system(self):
        # Allocate the nil object
        self._nilObject = Object(None)

        # Allocate the Metaclass classes
        self._metaclassClass = self.new_metaclass_class()

        # Allocate the rest of the system classes
        self._objectClass     = self.new_system_class()
        self._nilClass        = self.new_system_class()
        self._classClass      = self.new_system_class()
        self._arrayClass      = self.new_system_class()
        self._symbolClass     = self.new_system_class()
        self._methodClass     = self.new_system_class()
        self._integerClass    = self.new_system_class()
        self._bigintegerClass = self.new_system_class()
        self._frameClass      = self.new_system_class()
        self._primitiveClass  = self.new_system_class()
        self._stringClass     = self.new_system_class()
        self._doubleClass     = self.new_system_class()

        # Setup the class reference for the nil object
        self._nilObject.set_class(self._nilClass)

        # Initialize the system classes
        self._initialize_system_class(self._objectClass,                  None, "Object")
        self._initialize_system_class(self._classClass,      self._objectClass, "Class")
        self._initialize_system_class(self._metaclassClass,   self._classClass, "Metaclass")
        self._initialize_system_class(self._nilClass,        self._objectClass, "Nil")
        self._initialize_system_class(self._arrayClass,      self._objectClass, "Array")
        self._initialize_system_class(self._methodClass,      self._arrayClass, "Method")
        self._initialize_system_class(self._symbolClass,     self._objectClass, "Symbol")
        self._initialize_system_class(self._integerClass,    self._objectClass, "Integer")
        self._initialize_system_class(self._bigintegerClass, self._objectClass, "BigInteger")
        self._initialize_system_class(self._frameClass,       self._arrayClass, "Frame")
        self._initialize_system_class(self._primitiveClass,  self._objectClass, "Primitive")
        self._initialize_system_class(self._stringClass,     self._objectClass, "String")
        self._initialize_system_class(self._doubleClass,     self._objectClass, "Double")

        # Load methods and fields into the system classes
        self._load_system_class(self._objectClass)
        self._load_system_class(self._classClass)
        self._load_system_class(self._metaclassClass)
        self._load_system_class(self._nilClass)
        self._load_system_class(self._arrayClass)
        self._load_system_class(self._methodClass)
        self._load_system_class(self._symbolClass)
        self._load_system_class(self._integerClass)
        self._load_system_class(self._bigintegerClass)
        self._load_system_class(self._frameClass)
        self._load_system_class(self._primitiveClass)
        self._load_system_class(self._stringClass)
        self._load_system_class(self._doubleClass)

        # Load the generic block class
        self._blockClass = self.load_class(self.symbol_for("Block"))

        # Setup the true and false objects
        trueClassName    = self.symbol_for("True")
        trueClass        = self.load_class(trueClassName)
        self._trueObject = self.new_instance(trueClass)

        falseClassName    = self.symbol_for("False")
        falseClass        = self.load_class(falseClassName)
        self._falseObject = self.new_instance(falseClass)

        # Load the system class and create an instance of it
        self._systemClass = self.load_class(self.symbol_for("System"))
        system_object = self.new_instance(self._systemClass)

        # Put special objects and classes into the dictionary of globals
        self.set_global(self.symbol_for("nil"),    self._nilObject)
        self.set_global(self.symbol_for("true"),   self._trueObject)
        self.set_global(self.symbol_for("false"),  self._falseObject)
        self.set_global(self.symbol_for("system"), system_object)
        self.set_global(self.symbol_for("System"), self._systemClass)
        self.set_global(self.symbol_for("Block"),  self._blockClass)

        self.set_global(self.symbol_for("Nil"),    self.nilClass)
        
        self.set_global( trueClassName,  trueClass)
        self.set_global(falseClassName, falseClass)

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
        result = Array(self._nilObject, length)
        result.set_class(self._arrayClass)

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
        result = Block(self._nilObject, method, context_frame)
        result.set_class(self._get_block_class(arguments))

        # Return the freshly allocated block
        return result

    def new_class(self, class_class):
        # Allocate a new class and set its class to be the given class class
        result = Class(self, class_class.get_number_of_instance_fields())
        result.set_class(class_class)

        # Return the freshly allocated class
        return result

    def new_frame(self, previous_frame, method, context):
        # Compute the maximum number of stack locations (including arguments,
        # locals and extra buffer to support doesNotUnderstand) and set the
        # number of indexable fields accordingly
        length = (method.get_number_of_arguments() +
                  method.get_number_of_locals().get_embedded_integer() +
                  method.get_maximum_number_of_stack_elements().get_embedded_integer() + 2)

        # Allocate a new frame and set its class to be the frame class
        result = Frame(self._nilObject, length, method, context, previous_frame)
        result.set_class(self._frameClass)

        # Reset the stack pointer and the bytecode index
        result.reset_stack_pointer()
        result.set_bytecode_index(0)

        # Return the freshly allocated frame
        return result

    def new_method(self, signature, num_bytecodes, num_literals,
                   num_locals, maximum_number_of_stack_elements):
        # Allocate a new method and set its class to be the method class
        result = Method(self._nilObject,
                        num_literals,
                        num_locals,
                        maximum_number_of_stack_elements,
                        num_bytecodes,
                        signature)
        result.set_class(self._methodClass)

        # Return the freshly allocated method
        return result

    def new_instance(self, instance_class):
        # Allocate a new instance and set its class to be the given class
        result = Object(self._nilObject, instance_class.get_number_of_instance_fields())
        result.set_class(instance_class)
 
        # Return the freshly allocated instance
        return result

 
    def new_integer(self, value):
        # Allocate a new integer and set its class to be the integer class
        result = Integer(self._nilObject, value)
        result.set_class(self._integerClass)
     
        # Return the freshly allocated integer
        return result
 
    def new_biginteger(self, value):
        # Allocate a new integer and set its class to be the integer class
        result = BigInteger(self._nilObject, value)
        result.set_class(self._bigintegerClass)
 
        # Return the freshly allocated integer
        return result
 
 
    def new_double(self, value):
        # Allocate a new integer and set its class to be the double class
        result = Double(self._nilObject, value)
        result.set_class(self._doubleClass)
 
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
        result = String(self._nilObject, embedded_string)
        result.set_class(self._stringClass)

        # Return the freshly allocated string
        return result
    
    def new_symbol(self, string):
        # Allocate a new symbol and set its class to be the symbol class
        result = Symbol(self._nilObject, string)
        result.set_class(self._symbolClass)

        # Insert the new symbol into the symbol table
        self._symbol_table.insert(result)

        # Return the freshly allocated symbol
        return result
      
    def new_system_class(self):
        # Allocate the new system class
        system_class = Class(self)

        # Setup the metaclass hierarchy
        system_class.set_class(Class(self))
        system_class.get_class().set_class(self._metaclassClass)

        # Return the freshly allocated system class
        return system_class
    
    def _initialize_system_class(self, system_class, super_class, name):
        # Initialize the superclass hierarchy
        if super_class:
            system_class.set_super_class(super_class)
            system_class.get_class().set_super_class(super_class.get_class())
        else:
            system_class.get_class().set_super_class(self._classClass)
    

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
            return self._blockClass
        
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
        result.add_instance_primitive(Block.get_evaluation_primitive(number_of_arguments, self))

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

        if not result:
            error_println(system_class.get_name().get_string()
                   + " class could not be loaded. It is likely that the "
                   + " class path has not been initialized properly. "
                   + "Please make sure that the '-cp' parameter is given on the command-line.")
            self.exit(200)

        # Load primitives if necessary
        if result.has_primitives():
            result.load_primitives()

    def _load_class(self, name, system_class):
        # Try loading the class from all different paths
        for cpEntry in self._classpath:
            try:
                # Load the class from a file and return the loaded class
                result = sourcecode_compiler.compile_class_from_file(cpEntry, name.get_string(), system_class, self)
                if self._dump_bytecodes:
                    from som.compiler.disassembler import Disassembler
                    Disassembler.dump(result.get_class())
                    Disassembler.dump(result)

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
            from som.compiler.disassembler import Disassembler
            Disassembler.dump(result)
        return result

    @classmethod
    def error_print(cls, msg):
        print(msg, file=sys.stderr, end="")

    @classmethod
    def error_println(cls, msg = ""):
        print(msg, file=sys.stderr)

    @classmethod
    def std_print(cls, msg):
        print(msg, end="")

    @classmethod
    def std_println(cls, msg=""):
        print(msg)

def main(args):
    u = Universe()
    u.interpret(args[1:])
    u.exit(0)

if __name__ == '__main__':
    main(sys.argv)
