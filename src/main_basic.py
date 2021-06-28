import os
import sys

from som.vm.current import current_universe

core_lib_path = os.path.dirname(os.path.abspath(__file__)) + "/../core-lib/"
current_universe.setup_classpath(
    core_lib_path + "Smalltalk:" + core_lib_path + "TestSuite/BasicInterpreterTests"
)
result = current_universe.execute_method(sys.argv[1], sys.argv[2])
print(result)
