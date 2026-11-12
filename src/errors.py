"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

EXIT_OK = 0
EXIT_LEXICAL = 11
EXIT_SYNTAX = 12
EXIT_SEMANTIC_TYPE = 13
EXIT_SEMANTIC = 14
EXIT_CODEGEN = 15
EXIT_INTERNAL = 19


class CompilerError(Exception):
    """Fatal compilation error with a specification exit code."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
