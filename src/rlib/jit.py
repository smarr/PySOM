try:
    from rpython.rlib.jit import elidable, elidable_promote, promote, unroll_safe, JitDriver, set_param, dont_look_inside, we_are_jitted, hint
except ImportError:
    "NOT_RPYTHON"
    def elidable(func):
        return func

    def elidable_promote(promote_args='all'):
        def decorator(func):
            return func
        return decorator

    def promote(value):
        return value

    def unroll_safe(func):
        return func

    def dont_look_inside(func):
        return func

    class JitDriver(object):
        def __init__(self, greens=None, reds=None, virtualizables=None,
                     get_jitcell_at=None, set_jitcell_at=None,
                     get_printable_location=None, confirm_enter_jit=None,
                     can_never_inline=None, should_unroll_one_iteration=None,
                     name='jitdriver', check_untranslated=True, vectorize=False,
                     get_unique_id=None, is_recursive=False, get_location=None):
            pass

        def jit_merge_point(_self, **livevars):
            pass

        def can_enter_jit(_self, **livevars):
            pass

    def set_param(_driver, _name, _value):
        pass

    def we_are_jitted():
        pass

    def hint(x, **kwds):
        return x
