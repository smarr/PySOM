try:
    from rpython.rtyper.lltypesystem.lloperation import llop
    from rpython.rtyper.lltypesystem.lltype import Signed, Unsigned
    from rpython.rtyper.lltypesystem.rffi import cast, UINT, INT

    def as_32_bit_unsigned_value(int_value):
        return cast(Signed, cast(UINT, int_value))

    def as_32_bit_signed_value(int_value):
        return cast(Signed, cast(INT, int_value))

    def unsigned_right_shift(left_val, right_val):
        u_l = cast(Unsigned, left_val)
        u_r = cast(Unsigned, right_val)

        return cast(Signed, u_l >> u_r)

    int_mod = llop.int_mod

except ImportError:
    "NOT_RPYTHON"
    def int_mod(_type, left, right):
        if left > 0:
            return abs(left) % abs(right)
        else:
            return 0 - (abs(left) % abs(right))

    def as_32_bit_unsigned_value(int_value):
        return int_value & 0xFFFFFFFF

    def as_32_bit_signed_value(int_value):
        is_negative = (int_value & 0x80000000) == 0x80000000
        value = int_value & 0x7FFFFFFF
        if is_negative:
            value = 0 - (0x80000000 - value)
        return value

    def unsigned_right_shift(left_val, right_val):
        return left_val >> right_val

    Signed = 1
    Unsigned = 2
