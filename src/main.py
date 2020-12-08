import sys
from som.compiler.parse_error import ParseError
from som.vm.universe import main, Exit


try:
    main(sys.argv)
except Exit as e:
    sys.exit(e.code)
except ParseError as e:
    from som.vm.universe import error_println

    error_println(str(e))
    sys.exit(1)

sys.exit(0)
