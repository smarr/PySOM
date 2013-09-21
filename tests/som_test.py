import unittest
from parameterized import parameterized
from som.vm.universe import Universe

class SomTest(unittest.TestCase):
    @parameterized.expand([
        ("Array"         ,),
        ("BigInteger"    ,),
        ("Block"         ,),
        ("ClassLoading"  ,),

        ("Closure"       ,),
        ("Coercion"      ,),
        ("CompilerReturn",),
        ("Double"        ,),

        ("Empty"         ,),
        ("Hash"          ,),
        ("Integer"       ,),
        ("ObjectSize"    ,),

        ("Preliminary"   ,),
        ("Reflection"    ,),
        ("SelfBlock"     ,),
        ("Super"         ,),

        ("String"        ,),
        ("Symbol"        ,),
        ("Vector"        ,)])
    def test_som_test(self, test_name):
        args = ["-cp", "Smalltalk", "TestSuite/TestHarness.som", test_name]
        u = Universe(True)
        u.interpret(args)
        
        self.assertEquals(0, u.last_exit_code())
