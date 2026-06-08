"""
Syntactic Analyzer for VYPlanguage
Uses PLY yacc with LALR parsing
"""

import ply.yacc as yacc
from lexer import tokens, lexer

# Precedence rules according to VYPlanguage specification
precedence = (
    ('left', 'OR'),                    # 0
    ('left', 'AND'),                   # 1
    ('left', 'EQUALS', 'NOT_EQUALS'),  # 4
    ('left', 'LESS_THAN', 'GREATER_THAN', 'LESS_EQUAL', 'GREATER_EQUAL'),  # 5
    ('left', 'PLUS', 'MINUS'),         # 6
    ('left', 'MULTIPLY', 'DIVIDE'),    # 7
    ('right', 'NOT'),                  # 8
    ('right', 'UMINUS'),               # 9
    ('left', 'DOT'),                   # 10
    ('right', 'NEW'),                  # 11
    ('right', 'ASSIGN'),               # Assignment
)

# Grammar rules for VYPlanguage
def p_program(p):
    """program : global_definitions"""
    p[0] = ('program', p[1])

def p_global_definitions(p):
    """global_definitions : global_definitions global_definition
                         | global_definition"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_global_definition(p):
    """global_definition : function_definition
                        | class_definition"""
    p[0] = p[1]

def p_function_definition(p):
    """function_definition : type IDENTIFIER LEFT_PAREN param_list RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    p[0] = ('function', p[1], p[2], p[4], p[7])

def p_class_definition(p):
    """class_definition : CLASS IDENTIFIER COLON IDENTIFIER LEFT_BRACE class_members RIGHT_BRACE"""
    p[0] = ('class', p[2], p[4], p[6])

def p_class_members(p):
    """class_members : class_members class_member
                     | class_member
                     | empty"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_class_member(p):
    """class_member : variable_definition
                   | method_definition"""
    p[0] = p[1]

def p_method_definition(p):
    """method_definition : type IDENTIFIER LEFT_PAREN param_list RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    p[0] = ('method', p[1], p[2], p[4], p[7])

def p_param_list(p):
    """param_list : param_list COMMA param
                  | param
                  | VOID
                  | empty"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2 and p[1] != 'void' and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_param(p):
    """param : data_type IDENTIFIER"""
    p[0] = ('param', p[1], p[2])

def p_type(p):
    """type : data_type
            | VOID"""
    p[0] = p[1]

def p_data_type(p):
    """data_type : prim_type
                 | IDENTIFIER"""
    p[0] = p[1]

def p_prim_type(p):
    """prim_type : INT
                 | STRING"""
    p[0] = p[1]

def p_statement_list(p):
    """statement_list : statement_list statement
                     | statement
                     | empty"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_statement(p):
    """statement : variable_definition
                 | assignment_statement
                 | if_statement
                 | while_statement
                 | function_call_statement
                 | method_call_statement
                 | return_statement
                 | block_statement"""
    p[0] = p[1]

def p_variable_definition(p):
    """variable_definition : data_type variable_list SEMICOLON"""
    p[0] = ('var_def', p[1], p[2])

def p_variable_list(p):
    """variable_list : variable_list COMMA IDENTIFIER
                     | IDENTIFIER"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_assignment_statement(p):
    """assignment_statement : IDENTIFIER ASSIGN expression SEMICOLON"""
    p[0] = ('assign', p[1], p[3])

def p_if_statement(p):
    """if_statement : IF LEFT_PAREN expression RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE ELSE LEFT_BRACE statement_list RIGHT_BRACE
                    | IF LEFT_PAREN expression RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    if len(p) == 12:
        p[0] = ('if_else', p[3], p[6], p[10])
    else:
        p[0] = ('if', p[3], p[6])

def p_while_statement(p):
    """while_statement : WHILE LEFT_PAREN expression RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    p[0] = ('while', p[3], p[6])

def p_function_call_statement(p):
    """function_call_statement : IDENTIFIER LEFT_PAREN arg_list RIGHT_PAREN SEMICOLON"""
    p[0] = ('function_call', p[1], p[3])

def p_method_call_statement(p):
    """method_call_statement : expression DOT IDENTIFIER LEFT_PAREN arg_list RIGHT_PAREN SEMICOLON"""
    p[0] = ('method_call', p[1], p[3], p[5])

def p_return_statement(p):
    """return_statement : RETURN expression SEMICOLON
                        | RETURN SEMICOLON"""
    if len(p) == 4:
        p[0] = ('return', p[2])
    else:
        p[0] = ('return', None)

def p_block_statement(p):
    """block_statement : LEFT_BRACE statement_list RIGHT_BRACE"""
    p[0] = ('block', p[2])

def p_arg_list(p):
    """arg_list : arg_list COMMA expression
                | expression
                | empty"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_expression(p):
    """expression : binary_expression
                 | unary_expression
                 | primary_expression"""
    p[0] = p[1]

def p_binary_expression(p):
    """binary_expression : expression PLUS expression
                         | expression MINUS expression
                         | expression MULTIPLY expression
                         | expression DIVIDE expression
                         | expression EQUALS expression
                         | expression NOT_EQUALS expression
                         | expression LESS_THAN expression
                         | expression GREATER_THAN expression
                         | expression LESS_EQUAL expression
                         | expression GREATER_EQUAL expression
                         | expression AND expression
                         | expression OR expression"""
    p[0] = ('binary', p[2], p[1], p[3])

def p_unary_expression(p):
    """unary_expression : NOT expression
                        | MINUS expression %prec UMINUS"""
    p[0] = ('unary', p[1], p[2])

def p_primary_expression(p):
    """primary_expression : IDENTIFIER
                          | INTEGER_LITERAL
                          | STRING_LITERAL
                          | THIS
                          | SUPER
                          | NEW IDENTIFIER
                          | LEFT_PAREN type RIGHT_PAREN expression
                          | IDENTIFIER LEFT_PAREN arg_list RIGHT_PAREN
                          | expression DOT IDENTIFIER LEFT_PAREN arg_list RIGHT_PAREN
                          | expression DOT IDENTIFIER
                          | LEFT_PAREN expression RIGHT_PAREN"""
    if len(p) == 2:
        p[0] = ('primary', p[1])
    elif len(p) == 3:
        p[0] = ('new', p[2])
    elif len(p) == 5 and p[1] == '(':
        p[0] = ('cast', p[2], p[4])
    elif len(p) == 5 and p[2] == '(':
        p[0] = ('function_call_expr', p[1], p[3])
    elif len(p) == 7 and p[2] == '.':
        p[0] = ('method_call_expr', p[1], p[3], p[5])
    elif len(p) == 4 and p[2] == '.':
        p[0] = ('field_access', p[1], p[3])
    elif len(p) == 4 and p[1] == '(':
        p[0] = p[2]

def p_empty(p):
    """empty :"""
    p[0] = None

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' on line {p.lineno}")
    else:
        print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc()

def parse(input_text):
    """Parse input text and return AST"""
    return parser.parse(input_text, lexer=lexer)

if __name__ == "__main__":
    # Test the parser with VYPlanguage example
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
    
    ast = parse(test_input)
    print("AST:", ast)