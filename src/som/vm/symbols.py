# pylint: disable=invalid-name
from rlib.jit import elidable
from som.vmobjects.symbol import Symbol

_symbol_table = {}


@elidable
def symbol_for(string):
    # Lookup the symbol in the symbol table
    result = _symbol_table.get(string, None)
    if result is not None:
        return result

    result = Symbol(string)
    # Insert the new symbol into the symbol table
    _symbol_table[string] = result
    return result


sym_array = symbol_for("Array")
sym_object = symbol_for("Object")

sym_nil = symbol_for("nil")
sym_true = symbol_for("true")
sym_false = symbol_for("false")

sym_plus = symbol_for("+")
sym_minus = symbol_for("-")
sym_multi = symbol_for("*")
sym_dbl_div = symbol_for("//")

sym_equal = symbol_for("=")
sym_equal_equal = symbol_for("==")

sym_is_nil = symbol_for("isNil")
sym_not_nil = symbol_for("notNil")

sym_array_size_placeholder = symbol_for("ArraySizeLiteralPlaceholder")

sym_new_msg = symbol_for("new:")
sym_at_msg = symbol_for("at:")
sym_at_put_msg = symbol_for("at:put:")
