#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test.
#
import py
from rpython import conftest  # pylint: disable=import-error
from rpython.jit.metainterp.test.test_ajit import LLJitMixin  # pylint: disable=E

from som.vm.current import current_universe
from som.vm.symbols import symbol_for
from som.vm.universe import Exit

from som.compiler.sourcecode_compiler import compile_class_from_string


class Option:
    view = False
    viewloops = True


conftest.option = Option

main_path = py.path.local(__file__).dirpath().dirpath()  # pylint: disable=no-member

cp = main_path.join("Smalltalk").strpath
benchmark_cp = cp + ":" + main_path.join("Examples/Benchmarks").strpath


class TestLLtype(LLJitMixin):
    @staticmethod
    def _compile_and_lookup(source, start, classpath):
        universe = current_universe
        universe.setup_classpath(classpath)
        universe._initialize_object_system()  # pylint: disable=protected-access
        cls = compile_class_from_string(source, None, universe)
        obj = universe.new_instance(cls)
        invokable = cls.lookup_invokable(symbol_for(start))
        return universe, obj, invokable

    def _run_meta_interp(self, program, main_method, classpath=cp):
        _universe, rcvr, invokable = self._compile_and_lookup(
            program, main_method, classpath
        )

        def interp_w():
            try:
                invokable.invoke_1(rcvr)
            except Exit as exit_ex:
                return exit_ex.code
            return -1

        self.meta_interp(
            interp_w, [], listcomp=True, listops=True, backendopt=True, inline=True
        )

    def _eval_expr(self, simple_expr, classpath=cp):
        class_def = """C_0 = ( run = ( %s ) )""" % simple_expr
        self._run_meta_interp(class_def, "run", classpath)

    def test_delta_blue(self):
        delta_blue_cp = (
            cp + ":" + main_path.join("Examples/Benchmarks/DeltaBlue").strpath
        )
        self._eval_expr(
            """Planner chainTest: 100.
                           Planner projectionTest: 100""",
            delta_blue_cp,
        )

    def test_inc(self):
        self._run_meta_interp(
            """
            C_0 = (
                run = ( | tmp |
                        tmp := 1.
                        10000 timesRepeat: [
                          tmp := tmp + 1 ].
                        ^tmp
                )
            )
            """,
            "run",
        )

    def test_pure_while(self):
        self._run_meta_interp(
            """
            C_0 = (
                run = ( | tmp |
                        tmp := 1.
                        [ tmp < 10000 ] whileTrue: [
                            tmp := tmp + 1 ].
                        ^tmp
                )
            )
            """,
            "run",
        )

    def test_dispatch(self):
        self._run_meta_interp(
            """
            Dispatch = (
                method: n = ( ^ n )
                run = ( 1 to: 20000 do: [:i | self method: i ] ) )
            """,
            "run",
        )

    def test_while_loop(self):
        self._run_meta_interp(
            """
    WhileLoop = (
            singleRun = (
        | sum |
        sum := 0.
        [sum < 1000]
            whileTrue:
                [sum := sum + 1].
        ^ sum
    )

    benchmark = (
        | sum |
        sum := 0.
        [sum < 20000]
            whileTrue:
                [sum := sum + self singleRun].
        ^ sum
    ) ) """,
            "benchmark",
        )

    def test_rec(self):
        self._run_meta_interp(
            """
            C_1 = (
                count: n = ( ^ (n > 0)
                                 ifTrue: [self count: n - 1]
                                 ifFalse: [n]
                )
                run = ( ^ self count: 100000 )
            )
            """,
            "run",
        )

    def test_sieve(self):
        self._run_meta_interp(
            """
           "Adapted from Sieve.som"
            Sieve = (
                benchmark = (
                    | flags result |
                    flags  := Array new: 5000.
                    result := self sieve: flags size: 5000.
                    ^ (result = 669)
                )

                sieve: flags size: size = (
                    | primeCount |
                    primeCount := 0.
                    flags putAll: true.
                    2 to: size do: [ :i |
                        (flags at: i - 1) ifTrue: [
                            | k |
                            primeCount := primeCount + 1.
                            k := i + i.
                            [ k <= size ] whileTrue: [
                                flags at: k - 1 put: false. k := k + i ]]].
                    ^primeCount
                )
            )""",
            "benchmark",
        )

    def test_fibonacci(self):
        self._run_meta_interp(
            """Fibonacci = (
    benchmark = ( | result |
        result := self fibonacci: 20.
        (result = 10946) ifFalse: [self error: 'Wrong result: ' + result + ' should be: 10946' ])

    fibonacci: n = (
        ^(n <= 1) ifTrue:  1 ifFalse: [ (self fibonacci: (n - 1)) + (self fibonacci: (n - 2)) ])
)        """,
            "benchmark",
        )

    def test_while_bench(self):
        self._run_meta_interp(
            """WhileLoop = (

    singleRun = (
        | sum |
        sum := 0.
        [sum < 1000]
            whileTrue:
                [sum := sum + 1].
        ^ sum
    )

    benchmark = (
        | sum |
        sum := 0.
        [sum < 20000]
            whileTrue:
                [sum := sum + self singleRun].
        ^ sum
    )

)
""",
            "benchmark",
        )

    def test_field(self):
        self._run_meta_interp(
            """
           "Adapted from FieldLoop.som"
            FieldLoop = (
                | counter |

                benchmark = ( | iter |
                    counter := 0.
                    iter := 20000.

                    [ iter > 0 ] whileTrue: [
                      iter := iter - 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.

                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.

                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.

                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.

                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.

                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.
                      counter := counter + 1.]
                )
            )""",
            "benchmark",
        )

    def test_inst_at(self):
        self._run_meta_interp(
            """
            FieldLoop = (
                | counter |

                benchmark = ( | iter |
                    counter := 0.
                    iter := 20000.

                    [ iter > 0 ] whileTrue: [
                      iter := iter - 1.
                      self instVarAt: 1 put: (self instVarAt: 1)]
                )
            )""",
            "benchmark",
        )

    def test_tree_sort(self):
        self._eval_expr("""TreeSort benchmark""", benchmark_cp)

    def test_mandelbrot(self):
        self._eval_expr("""Mandelbrot benchmark""", benchmark_cp)

    def test_integer_loop(self):
        self._eval_expr("""IntegerLoop benchmark""", benchmark_cp)
