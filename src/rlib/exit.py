class Exit(Exception):
    """
    Use an exit exception to end program execution.
    We don't use sys.exit because it is a little problematic with RPython.
    """

    def __init__(self, code):  # pylint: disable=super-init-not-called
        self.code = code
