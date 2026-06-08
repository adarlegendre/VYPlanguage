"""
Lexical Analyzer for VYPlanguage
Uses PLY lex for tokenization
"""

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

# Token names
tokens = [
    # Identifiers and literals
    'IDENTIFIER', 'INTEGER_LITERAL', 'STRING_LITERAL',
    
    # Operators
    'ASSIGN', 'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE',
    'EQUALS', 'NOT_EQUALS', 'LESS_THAN', 'GREATER_THAN',
    'LESS_EQUAL', 'GREATER_EQUAL', 'AND', 'OR', 'NOT',
    
    # Delimiters
    'LEFT_PAREN', 'RIGHT_PAREN', 'LEFT_BRACE', 'RIGHT_BRACE',
    'SEMICOLON', 'COMMA', 'DOT', 'COLON',
    
    # Comments
    'COMMENT', 'BLOCK_COMMENT',
] + list(reserved.values())

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
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_INTEGER_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r'"(?:[^"\\]|\\.)*"'
    # Handle escape sequences: \n, \t, \\, \"
    t.value = t.value[1:-1]  # Remove quotes
    t.value = t.value.replace('\\n', '\n')
    t.value = t.value.replace('\\t', '\t')
    t.value = t.value.replace('\\\\', '\\')
    t.value = t.value.replace('\\"', '"')
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
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

def tokenize(input_text):
    """Tokenize input text and return list of tokens"""
    lexer.input(input_text)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens.append(tok)
    return tokens

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
