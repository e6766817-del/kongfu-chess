"""Domain error codes and exceptions for board-fixture validation.

Error-code strings are defined exactly once here; every other module
refers to them by name instead of repeating the literal.
"""

ROW_WIDTH_MISMATCH = "ERROR ROW_WIDTH_MISMATCH"
UNKNOWN_TOKEN = "ERROR UNKNOWN_TOKEN"


class BoardFixtureError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class RowWidthMismatchError(BoardFixtureError):
    def __init__(self):
        super().__init__(ROW_WIDTH_MISMATCH)


class UnknownTokenError(BoardFixtureError):
    def __init__(self):
        super().__init__(UNKNOWN_TOKEN)
