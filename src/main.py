import sys
from som.compiler.parse_error import ParseError
from som.vm.universe import main, Exit


try:
    main(sys.argv)
except Exit as ex:
    sys.exit(ex.code)
except ParseError as ex:
    from som.vm.universe import error_println

    error_println(str(ex))
    sys.exit(1)

sys.exit(0)
