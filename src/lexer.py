"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

import sys
from typing import Optional

import ply.lex as lex

# Reserved keywords according to VYPlanguage specification
reserved = {
    'class': 'CLASS',
    'else': 'ELSE',
    'if': 'IF',
    'int': 'INT',
    'new': 'NEW',
    'return': 'RETURN',
    'string': 'STRING',
    'super': 'SUPER',
    'this': 'THIS',
    'void': 'VOID',
    'while': 'WHILE',
}

# Token names (comments are discarded in t_COMMENT / t_BLOCK_COMMENT and are not tokens)
tokens = [
    # Identifiers and literals
    # TYPE_ID = class name (incl. Object); disambiguates (Type)cast vs (expr)
    'IDENTIFIER', 'TYPE_ID', 'INTEGER_LITERAL', 'STRING_LITERAL',
    
    # Operators
    'ASSIGN', 'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE',
    'EQUALS', 'NOT_EQUALS', 'LESS_THAN', 'GREATER_THAN',
    'LESS_EQUAL', 'GREATER_EQUAL', 'AND', 'OR', 'NOT',
    
    # Delimiters
    'LEFT_PAREN', 'RIGHT_PAREN', 'LEFT_BRACE', 'RIGHT_BRACE',
    'SEMICOLON', 'COMMA', 'DOT', 'COLON',
] + list(reserved.values())

# Class names visible for the current parse (Object + user classes).
type_names = {"Object"}

# Token regex patterns
t_ASSIGN = r'='
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULTIPLY = r'\*'
t_DIVIDE = r'/'
t_EQUALS = r'=='
t_NOT_EQUALS = r'!='
t_LESS_THAN = r'<'
t_GREATER_THAN = r'>'
t_LESS_EQUAL = r'<='
t_GREATER_EQUAL = r'>='
t_AND = r'&&'
t_OR = r'\|\|'
t_NOT = r'!'
t_LEFT_PAREN = r'\('
t_RIGHT_PAREN = r'\)'
t_LEFT_BRACE = r'\{'
t_RIGHT_BRACE = r'\}'
t_SEMICOLON = r';'
t_COMMA = r','
t_DOT = r'\.'
t_COLON = r':'

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value in reserved:
        t.type = reserved[t.value]
    elif t.value in type_names:
        t.type = "TYPE_ID"
    else:
        t.type = "IDENTIFIER"
    return t


def set_type_names(names):
    """Set class/type names recognized as TYPE_ID for the next tokenize/parse."""
    global type_names
    type_names = set(names) | {"Object"}


def collect_class_names(text: str):
    """Pre-scan source for 'class Id' declarations (spec: visible everywhere)."""
    import re

    names = {"Object"}
    for match in re.finditer(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", text):
        names.add(match.group(1))
    return names

def t_INTEGER_LITERAL(t):
    r'\d+'
    raw = t.value
    # Spec: [0-9]+ without superfluous leading zeros
    if len(raw) > 1 and raw[0] == "0":
        print(
            f"Lexical error: superfluous leading zero in integer '{raw}' "
            f"at line {t.lineno}",
            file=sys.stderr,
        )
        t.lexer.lex_error = True
        return None
    t.value = int(raw)
    return t


def _decode_string_literal(raw: str, lineno: int, lexer) -> Optional[str]:
    """Decode VYPlanguage string body; return None on lexical error."""
    out = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch != "\\":
            if ord(ch) < 32:
                print(
                    f"Lexical error: non-printable character in string at line {lineno}",
                    file=sys.stderr,
                )
                lexer.lex_error = True
                return None
            out.append(ch)
            i += 1
            continue
        if i + 1 >= n:
            print(
                f"Lexical error: trailing backslash in string at line {lineno}",
                file=sys.stderr,
            )
            lexer.lex_error = True
            return None
        esc = raw[i + 1]
        if esc == "n":
            out.append("\n")
            i += 2
        elif esc == "t":
            out.append("\t")
            i += 2
        elif esc == "\\":
            out.append("\\")
            i += 2
        elif esc == '"':
            out.append('"')
            i += 2
        elif esc == "x":
            hexdigits = raw[i + 2 : i + 8]
            if len(hexdigits) != 6 or any(
                c not in "0123456789abcdefABCDEF" for c in hexdigits
            ):
                print(
                    f"Lexical error: invalid \\xhhhhhh escape at line {lineno}",
                    file=sys.stderr,
                )
                lexer.lex_error = True
                return None
            out.append(chr(int(hexdigits, 16)))
            i += 8
        else:
            print(
                f"Lexical error: invalid escape '\\{esc}' at line {lineno}",
                file=sys.stderr,
            )
            lexer.lex_error = True
            return None
    return "".join(out)


def t_STRING_LITERAL(t):
    r'"(?:[^"\\]|\\.)*"'
    body = t.value[1:-1]
    decoded = _decode_string_literal(body, t.lineno, t.lexer)
    if decoded is None:
        return None
    t.value = decoded
    return t

# Handle comments
def t_COMMENT(t):
    r'//.*'
    pass  # Ignore line comments

def t_BLOCK_COMMENT(t):
    r'/\*(?:[^*]|\*(?!/))*\*/'
    pass  # Ignore block comments

# Ignore whitespace
t_ignore = ' \t\r'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(
        f"Lexical error: illegal character '{t.value[0]}' at line {t.lineno}",
        file=sys.stderr,
    )
    t.lexer.lex_error = True
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()
lexer.lex_error = False

def tokenize(input_text):
    """Tokenize input text and return list of tokens.

    Sets lexer.lex_error if any illegal character was found.
    """
    lexer.lex_error = False
    lexer.lineno = 1
    lexer.input(input_text)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens.append(tok)
    return tokens


def had_lexical_error():
    """Return True if the last tokenize() call hit a lexical error."""
    return bool(getattr(lexer, "lex_error", False))

if __name__ == "__main__":
    # Test the lexer with VYPlanguage example
    test_input = """
    void main(void) {
        int a, res;
        print("Enter an integer to compute its factorial:");
        a = readInt();
        if (a < 0) {
            print("\\nFactorial of a negative integer is undefined!\\n");
        } else {
            res = 1;
            while (a > 0) {
                res = res * a;
                a = a - 1;
            }
            print("\\nThe result is: ", res, "\\n");
        }
    }
    """
    
    tokens = tokenize(test_input)
    for token in tokens:
        print(f"{token.type}: {token.value} (line {token.lineno})")
