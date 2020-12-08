import math

INFINITY = 1e200 * 1e200

try:
    from rpython.rlib.rfloat import formatd, DTSF_ADD_DOT_0, DTSF_STR_PRECISION, round_double

    def float_to_str(value):
        return formatd(value, "g", DTSF_STR_PRECISION, DTSF_ADD_DOT_0)

except ImportError:
    "NOT_RPYTHON"
    def float_to_str(value):
        return str(value)

    def round_double(x, ndigits):
        # round() from libm, which is not available on all platforms!
        # This version rounds away from zero.
        absx = abs(x)
        r = math.floor(absx + 0.5)
        if r - absx < 1.0:
            return math.copysign(r, x)
        else:
            # 'absx' is just in the wrong range: its exponent is precisely
            # the one for which all integers are representable but not any
            # half-integer.  It means that 'absx + 0.5' computes equal to
            # 'absx + 1.0', which is not equal to 'absx'.  So 'r - absx'
            # computes equal to 1.0.  In this situation, we can't return
            # 'r' because 'absx' was already an integer but 'r' is the next
            # integer!  But just returning the original 'x' is fine.
            return x
