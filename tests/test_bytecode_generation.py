# pylint: disable=redefined-outer-name
import pytest
from rlib.string_stream import StringStream

from som.compiler.bc.disassembler import dump_method
from som.compiler.bc.method_generation_context import MethodGenerationContext
from som.compiler.bc.parser import Parser
from som.compiler.class_generation_context import ClassGenerationContext
from som.interp_type import is_ast_interpreter
from som.interpreter.bc.bytecodes import Bytecodes, bytecode_length
from som.vm.current import current_universe

pytestmark = pytest.mark.skipif(  # pylint: disable=invalid-name
    is_ast_interpreter(), reason="Tests are specific to bytecode interpreter"
)


def add_field(cgenc, name):
    cgenc.add_instance_field(current_universe.symbol_for(name))


def dump(mgenc):
    dump_method(mgenc, b"")


@pytest.fixture
def cgenc():
    gen_c = ClassGenerationContext(current_universe)
    gen_c.name = current_universe.symbol_for("Test")
    return gen_c


@pytest.fixture
def mgenc(cgenc):
    mgenc = MethodGenerationContext(current_universe, cgenc, None)
    mgenc.add_argument("self", None, None)
    return mgenc


@pytest.fixture
def bgenc(cgenc, mgenc):
    mgenc.signature = current_universe.symbol_for("test")
    bgenc = MethodGenerationContext(current_universe, cgenc, mgenc)
    return bgenc


def method_to_bytecodes(mgenc, source):
    parser = Parser(StringStream(source.strip()), "test", current_universe)
    parser.method(mgenc)
    return mgenc.get_bytecodes()


def block_to_bytecodes(bgenc, source):
    parser = Parser(StringStream(source), "test", current_universe)

    parser.nested_block(bgenc)
    return bgenc.get_bytecodes()


@pytest.mark.parametrize(
    "operator,bytecode",
    [
        ("+", Bytecodes.inc),
        ("-", Bytecodes.dec),
    ],
)
def test_inc_dec_bytecodes(mgenc, operator, bytecode):
    bytecodes = method_to_bytecodes(mgenc, "test = ( 1 OP 1 )".replace("OP", operator))

    assert len(bytecodes) == 3
    assert bytecodes[0] == Bytecodes.push_1
    assert bytecodes[1] == bytecode
    assert bytecodes[2] == Bytecodes.return_self


def test_empty_method_returns_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( )")

    assert len(bytecodes) == 1
    assert bytecodes[0] == Bytecodes.return_self


def test_explicit_return_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ self )")

    assert len(bytecodes) == 1
    assert bytecodes[0] == Bytecodes.return_self


def test_dup_pop_argument_pop(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test: arg = ( arg := 1. ^ self )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_argument == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_argument_pop_implicit_return_self(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test: arg = ( arg := 1 )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_argument == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_local_pop(mgenc):
    bytecodes = method_to_bytecodes(mgenc, "test = ( | local | local := 1. ^ self )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_local == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_field_0_pop(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( field := 1. ^ self )")

    assert len(bytecodes) == 3
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_field_0 == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[2]


def test_dup_pop_field_pop(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( field := 1. ^ self )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_field == bytecodes[1]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_field_return_self(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test: val = ( field := val )")

    assert len(bytecodes) == 5
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.pop_field_0 == bytecodes[3]
    assert Bytecodes.return_self == bytecodes[4]


def test_dup_pop_field_n_return_self(cgenc, mgenc):
    add_field(cgenc, "a")
    add_field(cgenc, "b")
    add_field(cgenc, "c")
    add_field(cgenc, "d")
    add_field(cgenc, "e")
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test: value = ( field := value )")

    assert len(bytecodes) == 7
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.pop_field == bytecodes[3]
    assert Bytecodes.return_self == bytecodes[6]


def test_send_dup_pop_field_return_local(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ field := self method )")

    assert len(bytecodes) == 8
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.send_1 == bytecodes[3]
    assert Bytecodes.dup == bytecodes[5]
    assert Bytecodes.pop_field_0 == bytecodes[6]
    assert Bytecodes.return_local == bytecodes[7]


def test_send_dup_pop_field_return_local_period(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(mgenc, "test = ( ^ field := self method. )")

    assert len(bytecodes) == 8
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.send_1 == bytecodes[3]
    assert Bytecodes.dup == bytecodes[5]
    assert Bytecodes.pop_field_0 == bytecodes[6]
    assert Bytecodes.return_local == bytecodes[7]


@pytest.mark.parametrize(
    "literal,bytecode",
    [
        ("0", Bytecodes.push_0),
        ("1", Bytecodes.push_1),
        ("-10", Bytecodes.push_constant_2),
        ("3333", Bytecodes.push_constant_2),
        ("'str'", Bytecodes.push_constant_2),
        ("#sym", Bytecodes.push_constant_2),
        ("1.1", Bytecodes.push_constant_2),
        ("-2342.234", Bytecodes.push_constant_2),
        ("true", Bytecodes.push_constant_2),
        ("false", Bytecodes.push_constant_2),
        ("nil", Bytecodes.push_nil),
        ("SomeGlobal", Bytecodes.push_global),
        ("[]", Bytecodes.push_block_no_ctx),
        ("[ self ]", Bytecodes.push_block),
    ],
)
def test_if_true_with_literal_return(mgenc, literal, bytecode):
    source = """
        test = (
            self method ifTrue: [ LITERAL ].
        )""".replace(
        "LITERAL", literal
    )
    bytecodes = method_to_bytecodes(mgenc, source)

    length = bytecode_length(bytecode)

    assert len(bytecodes) == 9 + length
    assert Bytecodes.push_argument == bytecodes[0]
    assert Bytecodes.send_1 == bytecodes[3]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[5]

    assert bytecode == bytecodes[7]

    assert Bytecodes.pop == bytecodes[7 + length]
    assert Bytecodes.return_self == bytecodes[7 + length + 1]


@pytest.mark.parametrize(
    "if_selector,jump_bytecode",
    [
        ("ifTrue:", Bytecodes.jump_on_false_top_nil),
        ("ifFalse:", Bytecodes.jump_on_true_top_nil),
    ],
)
def test_if_arg(mgenc, if_selector, jump_bytecode):
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
            #start.
            self method IF_SELECTOR [ arg ].
            #end
        )""".replace(
            "IF_SELECTOR", if_selector
        ),
    )

    assert len(bytecodes) == 16
    assert Bytecodes.push_constant_0 == bytecodes[0]
    assert Bytecodes.pop == bytecodes[1]
    assert Bytecodes.push_argument == bytecodes[2]
    assert Bytecodes.send_1 == bytecodes[5]
    assert jump_bytecode == bytecodes[7]
    assert bytecodes[8] == 5, "jump offset"

    assert Bytecodes.push_argument == bytecodes[9]
    assert bytecodes[10] == 1, "arg idx"
    assert bytecodes[11] == 0, "ctx level"
    assert Bytecodes.pop == bytecodes[12]
    assert Bytecodes.push_constant == bytecodes[13]
    assert Bytecodes.return_self == bytecodes[15]


def test_keyword_if_true_arg(mgenc):
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
            #start.
            (self key: 5) ifTrue: [ arg ].
            #end
        )""",
    )

    assert len(bytecodes) == 17
    assert Bytecodes.send_2 == bytecodes[6]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[8]
    assert bytecodes[9] == 5, "jump offset"

    assert Bytecodes.push_argument == bytecodes[10]
    assert bytecodes[11] == 1, "arg idx"
    assert bytecodes[12] == 0, "ctx level"
    assert Bytecodes.pop == bytecodes[13]
    assert Bytecodes.push_constant == bytecodes[14]


def test_if_true_and_inc_field(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
            #start.
            (self key: 5) ifTrue: [ field := field + 1 ].
            #end
        )""",
    )

    assert len(bytecodes) == 22
    assert Bytecodes.send_2 == bytecodes[6]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[8]
    assert bytecodes[9] == 10, "jump offset"

    assert Bytecodes.push_field == bytecodes[10]
    assert bytecodes[11] == 0, "field idx"
    assert bytecodes[12] == 0, "ctx level"
    assert Bytecodes.inc == bytecodes[13]
    assert Bytecodes.dup == bytecodes[14]
    assert Bytecodes.pop_field == bytecodes[15]
    assert bytecodes[16] == 0, "field idx"
    assert bytecodes[17] == 0, "ctx level"
    assert Bytecodes.pop == bytecodes[18]


def test_if_true_and_inc_arg(mgenc):
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
            #start.
            (self key: 5) ifTrue: [ arg + 1 ].
            #end
        )""",
    )

    assert len(bytecodes) == 18
    assert Bytecodes.send_2 == bytecodes[6]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[8]
    assert bytecodes[9] == 6, "jump offset"

    assert Bytecodes.push_argument == bytecodes[10]
    assert bytecodes[11] == 1, "arg idx"
    assert bytecodes[12] == 0, "ctx level"
    assert Bytecodes.inc == bytecodes[13]
    assert Bytecodes.pop == bytecodes[14]
    assert Bytecodes.push_constant == bytecodes[15]


@pytest.mark.parametrize(
    "if_selector,jump_bytecode",
    [
        ("ifTrue:", Bytecodes.jump_on_false_top_nil),
        ("ifFalse:", Bytecodes.jump_on_true_top_nil),
    ],
)
def test_if_return_non_local(mgenc, if_selector, jump_bytecode):
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
            #start.
            self method IF_SELECTOR [ ^ arg ].
            #end
        )""".replace(
            "IF_SELECTOR", if_selector
        ),
    )

    assert len(bytecodes) == 18
    assert Bytecodes.send_1 == bytecodes[5]
    assert jump_bytecode == bytecodes[7]
    assert bytecodes[8] == 7, "jump offset"

    assert Bytecodes.push_argument == bytecodes[9]
    assert bytecodes[10] == 1, "arg idx"
    assert bytecodes[11] == 0, "ctx level"
    assert Bytecodes.return_local == bytecodes[12]
    assert (
        Bytecodes.halt == bytecodes[13]
    ), "because the original return_non_local has length=2"
    assert Bytecodes.pop == bytecodes[14]


def test_nested_ifs(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
            true ifTrue: [
                false ifFalse: [
                  ^ field - arg
                ]
            ]
        )""",
    )

    assert len(bytecodes) == 19
    assert Bytecodes.push_global == bytecodes[0]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[2]
    assert bytecodes[3] == 16
    assert Bytecodes.jump_on_true_top_nil == bytecodes[6]
    assert Bytecodes.push_field == bytecodes[8]
    assert bytecodes[9] == 0, "field idx"
    assert bytecodes[10] == 0, "ctx_level"
    assert Bytecodes.push_argument == bytecodes[11]
    assert bytecodes[12] == 1, "arg idx"
    assert bytecodes[13] == 0, "ctx_level"
    assert Bytecodes.send_2 == bytecodes[14]
    assert Bytecodes.return_local == bytecodes[16]
    assert Bytecodes.halt == bytecodes[17]
    assert Bytecodes.return_self == bytecodes[18]


def test_nested_ifs_and_locals(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
          | a b c d |
          a := b.
          true ifTrue: [
            | e f g |
            e := 2.
            c := 3.
            false ifFalse: [
              | h i j |
              h := 1.
              ^ i - j - f - g - d ] ] )""",
    )

    assert len(bytecodes) == 54
    assert Bytecodes.push_local == bytecodes[0]
    assert bytecodes[1] == 1
    assert bytecodes[2] == 0

    assert Bytecodes.pop_local == bytecodes[3]
    assert bytecodes[4] == 0
    assert bytecodes[5] == 0

    assert Bytecodes.jump_on_false_top_nil == bytecodes[8]
    assert bytecodes[9] == 45, "jump offset"

    assert Bytecodes.pop_local == bytecodes[12]
    assert bytecodes[13] == 4
    assert bytecodes[14] == 0

    assert Bytecodes.pop_local == bytecodes[17]
    assert bytecodes[18] == 2
    assert bytecodes[19] == 0

    assert Bytecodes.jump_on_true_top_nil == bytecodes[22]
    assert bytecodes[23] == 31, "jump offset"

    assert Bytecodes.pop_local == bytecodes[25]
    assert bytecodes[26] == 7
    assert bytecodes[27] == 0

    assert Bytecodes.push_local == bytecodes[46]
    assert bytecodes[47] == 3
    assert bytecodes[48] == 0


def test_nested_ifs_and_non_inlined_blocks(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: arg = (
          | a |
          a := 1.
          true ifTrue: [
            | e |
            e := 0.
            [ a := 1. a ].
            false ifFalse: [
              | h |
              h := 1.
              [ h + a + e ].
              ^ h ] ].

          [ a ]
        )""",
    )

    assert len(bytecodes) == 35
    assert Bytecodes.push_global == bytecodes[4]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[6]
    assert bytecodes[7] == 25, "jump offset"
    assert Bytecodes.pop_local == bytecodes[9]
    assert bytecodes[10] == 1, "e var idx"
    assert bytecodes[11] == 0, "e ctx idx"

    block_method = mgenc.get_constant(12)
    assert block_method.get_bytecode(1) == Bytecodes.pop_local
    assert block_method.get_bytecode(2) == 0, "a var idx"
    assert block_method.get_bytecode(3) == 1, "a ctx level"

    assert Bytecodes.jump_on_true_top_nil == bytecodes[17]
    assert bytecodes[18] == 14, "jump offset"

    assert Bytecodes.pop_local == bytecodes[20]
    assert bytecodes[21] == 2, "h var idx"
    assert bytecodes[22] == 0, "h ctx idx"

    block_method = mgenc.get_constant(23)
    assert block_method.get_bytecode(0) == Bytecodes.push_local
    assert block_method.get_bytecode(1) == 2, "h var idx"
    assert block_method.get_bytecode(2) == 1, "h ctx level"

    assert block_method.get_bytecode(3) == Bytecodes.push_local
    assert block_method.get_bytecode(4) == 0, "a var idx"
    assert block_method.get_bytecode(5) == 1, "a ctx level"

    assert block_method.get_bytecode(8) == Bytecodes.push_local
    assert block_method.get_bytecode(9) == 1, "e var idx"
    assert block_method.get_bytecode(10) == 1, "e ctx level"

    block_method = mgenc.get_constant(32)
    assert block_method.get_bytecode(0) == Bytecodes.push_local
    assert block_method.get_bytecode(1) == 0, "a var idx"
    assert block_method.get_bytecode(2) == 1, "a ctx level"


def test_nested_non_inlined_blocks(cgenc, mgenc):
    add_field(cgenc, "field")
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test: a = ( | b |
          true ifFalse: [ | c |
            a. b. c.
            [:d |
              a. b. c. d.
              [:e |
                a. b. c. d. e ] ] ]
        )""",
    )

    assert len(bytecodes) == 19
    assert Bytecodes.jump_on_true_top_nil == bytecodes[2]
    assert bytecodes[3] == 16, "jump offset"
    assert Bytecodes.push_argument == bytecodes[4]
    assert bytecodes[5] == 1, "a var idx"
    assert bytecodes[6] == 0, "a ctx idx"

    assert Bytecodes.push_local == bytecodes[8]
    assert bytecodes[9] == 0, "b var idx"
    assert bytecodes[10] == 0, "b ctx idx"

    assert Bytecodes.push_local == bytecodes[12]
    assert bytecodes[13] == 1, "c var idx"
    assert bytecodes[14] == 0, "c ctx idx"

    block_method = mgenc.get_constant(16)
    assert block_method.get_bytecode(0) == Bytecodes.push_argument
    assert block_method.get_bytecode(1) == 1, "a var idx"
    assert block_method.get_bytecode(2) == 1, "a ctx level"

    assert block_method.get_bytecode(4) == Bytecodes.push_local
    assert block_method.get_bytecode(5) == 0, "b var idx"
    assert block_method.get_bytecode(6) == 1, "b ctx level"

    assert block_method.get_bytecode(8) == Bytecodes.push_local
    assert block_method.get_bytecode(9) == 1, "c var idx"
    assert block_method.get_bytecode(10) == 1, "c ctx level"

    assert block_method.get_bytecode(12) == Bytecodes.push_argument
    assert block_method.get_bytecode(13) == 1, "d var idx"
    assert block_method.get_bytecode(14) == 0, "d ctx level"

    block_method = block_method.get_constant(16)
    assert block_method.get_bytecode(0) == Bytecodes.push_argument
    assert block_method.get_bytecode(1) == 1, "a var idx"
    assert block_method.get_bytecode(2) == 2, "a ctx level"

    assert block_method.get_bytecode(4) == Bytecodes.push_local
    assert block_method.get_bytecode(5) == 0, "b var idx"
    assert block_method.get_bytecode(6) == 2, "b ctx level"

    assert block_method.get_bytecode(8) == Bytecodes.push_local
    assert block_method.get_bytecode(9) == 1, "c var idx"
    assert block_method.get_bytecode(10) == 2, "c ctx level"

    assert block_method.get_bytecode(12) == Bytecodes.push_argument
    assert block_method.get_bytecode(13) == 1, "d var idx"
    assert block_method.get_bytecode(14) == 1, "d ctx level"

    assert block_method.get_bytecode(16) == Bytecodes.push_argument
    assert block_method.get_bytecode(17) == 1, "e var idx"
    assert block_method.get_bytecode(18) == 0, "e ctx level"


def test_block_if_true_arg(bgenc):
    bytecodes = block_to_bytecodes(
        bgenc,
        """
        [:arg | #start.
            self method ifTrue: [ arg ].
            #end
        ]""",
    )

    assert len(bytecodes) == 16
    assert Bytecodes.send_1 == bytecodes[5]
    assert Bytecodes.jump_on_false_top_nil == bytecodes[7]
    assert bytecodes[8] == 5, "jump offset"

    assert Bytecodes.push_argument == bytecodes[9]
    assert bytecodes[10] == 1, "arg idx"
    assert bytecodes[11] == 0, "ctx level"
    assert Bytecodes.pop == bytecodes[12]
    assert Bytecodes.push_constant == bytecodes[13]


def test_block_if_true_method_arg(mgenc, bgenc):
    mgenc.add_argument("arg", None, None)
    bytecodes = block_to_bytecodes(
        bgenc,
        """
        [ #start.
            self method ifTrue: [ arg ].
            #end
        ]""",
    )

    assert len(bytecodes) == 16
    assert Bytecodes.jump_on_false_top_nil == bytecodes[7]
    assert bytecodes[8] == 5, "jump offset"

    assert Bytecodes.push_argument == bytecodes[9]
    assert bytecodes[10] == 1, "arg idx"
    assert bytecodes[11] == 1, "ctx level"
    assert Bytecodes.pop == bytecodes[12]
    assert Bytecodes.push_constant == bytecodes[13]


# def test_if_true_if_false_arg(mgenc):
#     bytecodes = method_to_bytecodes(
#         mgenc,
#         """
#         test: arg1 with: arg2 = (
#             #start.
#             self method ifTrue: [ arg1 ] ifFalse: [ arg2 ].
#             #end
#         )""",
#     )
#
#     dump(mgenc)
#     assert len(bytecodes) == 1
#
#
# def test_if_true_if_false_nlr_arg1(mgenc):
#     bytecodes = method_to_bytecodes(
#         mgenc,
#         """
#         test: arg1 with: arg2 = (
#             #start.
#             self method ifTrue: [ ^ arg1 ] ifFalse: [ arg2 ].
#             #end
#         )""",
#     )
#
#     dump(mgenc)
#     assert len(bytecodes) == 1
#
#
# def test_if_true_if_false_nlr_arg2(mgenc):
#     bytecodes = method_to_bytecodes(
#         mgenc,
#         """
#         test: arg1 with: arg2 = (
#             #start.
#             self method ifTrue: [ arg1 ] ifFalse: [ ^ arg2 ].
#             #end
#         )""",
#     )
#
#     dump(mgenc)
#     assert len(bytecodes) == 1
#
#
# def test_if_true_if_false_return(mgenc):
#     bytecodes = method_to_bytecodes(
#         mgenc,
#         """
#         test: arg1 with: arg2 = (
#             #start.
#             ^ self method ifTrue: [ ^ arg1 ] ifFalse: [ arg2 ]
#         )""",
#     )
#
#     dump(mgenc)
#     assert len(bytecodes) == 1
#
#
# def test_if_false_if_true_return(mgenc):
#     bytecodes = method_to_bytecodes(
#         mgenc,
#         """
#         test: arg1 with: arg2 = (
#             #start.
#             ^ self method ifFalse: [ ^ arg1 ] ifTrue: [ arg2 ]
#         )""",
#     )
#
#     dump(mgenc)
#     assert len(bytecodes) == 1


def test_if_push_constant_same(mgenc):
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test = (
          #a. #b. #c. #d.
          true ifFalse: [ #a. #b. #c. #d. ]
        )""",
    )

    assert len(bytecodes) == 22
    assert Bytecodes.push_constant_0 == bytecodes[0]
    assert Bytecodes.push_constant_1 == bytecodes[2]
    assert Bytecodes.push_constant_2 == bytecodes[4]
    assert Bytecodes.push_constant == bytecodes[6]
    assert bytecodes[7] == 3, "const idx"

    assert Bytecodes.jump_on_true_top_nil == bytecodes[11]
    assert bytecodes[12] == 10, "jump offset"

    assert Bytecodes.push_constant_0 == bytecodes[13]
    assert Bytecodes.push_constant_1 == bytecodes[15]
    assert Bytecodes.push_constant_2 == bytecodes[17]
    assert Bytecodes.push_constant == bytecodes[19]
    assert bytecodes[20] == 3, "const idx"


def test_if_push_constant_different(mgenc):
    bytecodes = method_to_bytecodes(
        mgenc,
        """
        test = (
          #a. #b. #c. #d.
          true ifFalse: [ #e. #f. #g. #h. ]
        )""",
    )

    assert len(bytecodes) == 25
    assert Bytecodes.push_constant_0 == bytecodes[0]
    assert Bytecodes.push_constant_1 == bytecodes[2]
    assert Bytecodes.push_constant_2 == bytecodes[4]
    assert Bytecodes.push_constant == bytecodes[6]
    assert bytecodes[7] == 3, "const idx"

    assert Bytecodes.jump_on_true_top_nil == bytecodes[11]
    assert bytecodes[12] == 13, "jump offset"

    assert Bytecodes.push_constant == bytecodes[13]
    assert bytecodes[14] == 6, "const idx"

    assert Bytecodes.push_constant == bytecodes[16]
    assert bytecodes[17] == 7, "const idx"

    assert Bytecodes.push_constant == bytecodes[19]
    assert bytecodes[20] == 8, "const idx"

    assert Bytecodes.push_constant == bytecodes[22]
    assert bytecodes[23] == 9, "const idx"


def test_block_dup_pop_argument_pop_return_arg(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1. arg ]")

    assert len(bytecodes) == 8
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.pop_argument == bytecodes[1]
    assert Bytecodes.push_argument == bytecodes[4]
    assert Bytecodes.return_local == bytecodes[7]


def test_block_dup_pop_argument_pop_implicit_return(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1 ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_argument == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_argument_pop_implicit_return_dot(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[:arg | arg := 1. ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_argument == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_local_return_local(bgenc):
    bytecodes = block_to_bytecodes(bgenc, "[| local | local := 1 ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_local == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_field_return_local(cgenc, bgenc):
    add_field(cgenc, "field")
    bytecodes = block_to_bytecodes(bgenc, "[ field := 1 ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_field == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


def test_block_dup_pop_field_return_local_dot(cgenc, bgenc):
    add_field(cgenc, "field")
    bytecodes = block_to_bytecodes(bgenc, "[ field := 1. ]")

    assert len(bytecodes) == 6
    assert Bytecodes.push_1 == bytecodes[0]
    assert Bytecodes.dup == bytecodes[1]
    assert Bytecodes.pop_field == bytecodes[2]
    assert Bytecodes.return_local == bytecodes[5]


@pytest.mark.parametrize(
    "if_selector,jump_bytecode",
    [
        ("ifTrue:", Bytecodes.jump_on_false_top_nil),
        ("ifFalse:", Bytecodes.jump_on_true_top_nil),
    ],
)
def test_block_if_return_non_local(bgenc, if_selector, jump_bytecode):
    bytecodes = block_to_bytecodes(
        bgenc,
        """
        [:arg |
            #start.
            self method IF_SELECTOR [ ^ arg ].
            #end
        ]""".replace(
            "IF_SELECTOR", if_selector
        ),
    )

    assert len(bytecodes) == 18
    assert Bytecodes.send_1 == bytecodes[5]
    assert jump_bytecode == bytecodes[7]
    assert bytecodes[8] == 7, "jump offset"

    assert Bytecodes.push_argument == bytecodes[9]
    assert bytecodes[10] == 1, "arg idx"
    assert bytecodes[11] == 0, "ctx level"
    assert Bytecodes.return_non_local == bytecodes[12]
    assert bytecodes[13] == 1
    assert Bytecodes.pop == bytecodes[14]
