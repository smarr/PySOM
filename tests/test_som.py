import pytest

from som.vm.universe import create_universe, set_current


@pytest.mark.parametrize("test_name", [
        "Array"         ,
        "Block"         ,
        "ClassLoading"  ,
        "ClassStructure",

        "Closure"       ,
        "Coercion"      ,
        "CompilerReturn",
        "DoesNotUnderstand",
        "Double"        ,

        "Empty"         ,
        "Global"        ,
        "Hash"          ,
        "Integer"       ,

        "Preliminary"   ,
        "Reflection"    ,
        "SelfBlock"     ,
        "SpecialSelectors",
        "Super"         ,

        "Set"           ,
        "String"        ,
        "Symbol"        ,
        "System"        ,
        "Vector"        ])
def test_som(test_name):
    print(test_name)
    args = ["-cp", "Smalltalk", "TestSuite/TestHarness.som", test_name]
    u = create_universe(True)
    set_current(u)
    u.interpret(args)

    assert 0 == u.last_exit_code()
