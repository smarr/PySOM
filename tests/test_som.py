import os
import pytest

from som.vm.current import current_universe


@pytest.mark.parametrize(
    "test_name",
    [
        "Array",
        "Block",
        "ClassLoading",
        "ClassStructure",
        "Closure",
        "Coercion",
        "CompilerReturn",
        "DoesNotUnderstand",
        "Double",
        "Empty",
        "Global",
        "Hash",
        "Integer",
        "Preliminary",
        "Reflection",
        "SelfBlock",
        "SpecialSelectors",
        "Super",
        "Set",
        "String",
        "Symbol",
        "System",
        "Vector",
    ],
)
def test_som(test_name):
    current_universe.reset(True)
    core_lib_path = os.path.dirname(os.path.abspath(__file__)) + "/../core-lib/"
    args = [
        "-cp",
        core_lib_path + "Smalltalk",
        core_lib_path + "TestSuite/TestHarness.som",
        test_name,
    ]

    current_universe.interpret(args)

    assert current_universe.last_exit_code() == 0
