"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

import sys
import ply.yacc as yacc
from lexer import tokens, lexer, set_type_names, collect_class_names

# Precedence rules according to VYPlanguage specification (Table 1).
# CAST is a ficticious token for (type)expr priority 9.
precedence = (
    ('left', 'OR'),                    # 0
    ('left', 'AND'),                   # 1
    ('left', 'EQUALS', 'NOT_EQUALS'),  # 4
    ('left', 'LESS_THAN', 'GREATER_THAN', 'LESS_EQUAL', 'GREATER_EQUAL'),  # 5
    ('left', 'PLUS', 'MINUS'),         # 6
    ('left', 'MULTIPLY', 'DIVIDE'),    # 7
    ('right', 'NOT'),                  # 8
    ('right', 'CAST'),                 # 9 casting
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

def p_any_id(p):
    """any_id : IDENTIFIER
              | TYPE_ID"""
    # Constructors are named after the class (TYPE_ID after pre-scan).
    p[0] = p[1]

def p_function_definition(p):
    """function_definition : type any_id LEFT_PAREN param_list RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    p[0] = ('function', p[1], p[2], p[4], p[7])

def p_class_definition(p):
    """class_definition : CLASS any_id COLON any_id LEFT_BRACE class_members RIGHT_BRACE"""
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
    """class_member : data_type any_id class_member_tail
                    | VOID any_id LEFT_PAREN param_list RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    # Disambiguate fields (int x; / int a, b;) from methods (int foo(void) {...}).
    # A shared data_type any_id prefix must not reduce as a field before '('.
    if len(p) == 4:
        kind, payload = p[3]
        if kind == "field":
            p[0] = ("var_def", p[1], [p[2]] + payload)
        else:
            params, body = payload
            p[0] = ("method", p[1], p[2], params, body)
    else:
        p[0] = ("method", "void", p[2], p[4], p[7])


def p_class_member_tail(p):
    """class_member_tail : field_tail SEMICOLON
                         | LEFT_PAREN param_list RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    if len(p) == 3:
        p[0] = ("field", p[1])
    else:
        p[0] = ("method", (p[2], p[5]))


def p_field_tail(p):
    """field_tail : COMMA any_id field_tail
                  | empty"""
    if len(p) == 4:
        p[0] = [p[2]] + p[3]
    else:
        p[0] = []

def p_param_list(p):
    """param_list : param_list COMMA param
                  | param
                  | VOID"""
    # Spec §4.2: empty parameter list must be written as void, not ().
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif p[1] != 'void':
        p[0] = [p[1]]
    else:
        p[0] = []

def p_param(p):
    """param : data_type any_id"""
    p[0] = ('param', p[1], p[2])

def p_type(p):
    """type : data_type
            | VOID"""
    p[0] = p[1]

def p_data_type(p):
    """data_type : prim_type
                 | TYPE_ID
                 | IDENTIFIER"""
    # TYPE_ID for known classes; IDENTIFIER kept so unknown types are semantic errors.
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
    """variable_list : variable_list COMMA any_id
                     | any_id"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_assignment_statement(p):
    """assignment_statement : any_id ASSIGN expression SEMICOLON
                            | expression DOT any_id ASSIGN expression SEMICOLON"""
    if len(p) == 5:
        p[0] = ("assign", p[1], p[3])
    else:
        p[0] = ("field_assign", p[1], p[3], p[5])

def p_if_statement(p):
    """if_statement : IF LEFT_PAREN expression RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE ELSE LEFT_BRACE statement_list RIGHT_BRACE"""
    # Spec §4.6: if always requires an else branch.
    p[0] = ('if_else', p[3], p[6], p[10])

def p_while_statement(p):
    """while_statement : WHILE LEFT_PAREN expression RIGHT_PAREN LEFT_BRACE statement_list RIGHT_BRACE"""
    p[0] = ('while', p[3], p[6])

def p_function_call_statement(p):
    """function_call_statement : any_id LEFT_PAREN arg_list RIGHT_PAREN SEMICOLON"""
    p[0] = ('function_call', p[1], p[3])

def p_method_call_statement(p):
    """method_call_statement : expression DOT any_id LEFT_PAREN arg_list RIGHT_PAREN SEMICOLON"""
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
                 | cast_expression
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
    """unary_expression : NOT expression"""
    # Base language has no unary minus/plus (MINUS extension).
    p[0] = ('unary', p[1], p[2])

def p_cast_expression(p):
    """cast_expression : LEFT_PAREN prim_type RIGHT_PAREN expression %prec CAST
                       | LEFT_PAREN TYPE_ID RIGHT_PAREN expression %prec CAST"""
    # Only prim_type / TYPE_ID (not bare IDENTIFIER) so (a) stays grouping.
    # Spec priority 9: (string)a + s => ((string)a) + s
    p[0] = ("cast", p[2], p[4])

def p_primary_expression(p):
    """primary_expression : any_id
                          | INTEGER_LITERAL
                          | STRING_LITERAL
                          | THIS
                          | SUPER
                          | NEW any_id
                          | any_id LEFT_PAREN arg_list RIGHT_PAREN
                          | expression DOT any_id LEFT_PAREN arg_list RIGHT_PAREN
                          | expression DOT any_id
                          | LEFT_PAREN expression RIGHT_PAREN"""
    if len(p) == 2:
        # Tag literals vs identifiers so later phases can tell them apart
        # (lexer strips quotes from STRING_LITERAL values).
        tok_type = p.slice[1].type
        if tok_type == "INTEGER_LITERAL":
            p[0] = ("int_lit", p[1])
        elif tok_type == "STRING_LITERAL":
            p[0] = ("str_lit", p[1])
        elif tok_type == "THIS":
            p[0] = ("this",)
        elif tok_type == "SUPER":
            p[0] = ("super",)
        else:
            # any_id (IDENTIFIER or TYPE_ID name string)
            p[0] = ("var", p[1])
    elif len(p) == 3:
        p[0] = ("new", p[2])
    elif len(p) == 5 and p[2] == "(":
        p[0] = ("function_call_expr", p[1], p[3])
    elif len(p) == 7 and p[2] == ".":
        p[0] = ("method_call_expr", p[1], p[3], p[5])
    elif len(p) == 4 and p[2] == ".":
        p[0] = ("field_access", p[1], p[3])
    elif len(p) == 4 and p[1] == "(":
        p[0] = p[2]

def p_empty(p):
    """empty :"""
    p[0] = None

# Set by p_error during the last parse()
syntax_error = False

def p_error(p):
    global syntax_error
    syntax_error = True
    if p:
        print(
            f"Syntax error at '{p.value}' on line {p.lineno}",
            file=sys.stderr,
        )
    else:
        print("Syntax error at EOF", file=sys.stderr)

# Build the parser
parser = yacc.yacc(debug=False, write_tables=True)

def parse(input_text):
    """Parse input text and return AST.

    Sets module-level syntax_error if the parse failed.
    """
    global syntax_error
    syntax_error = False
    # Spec §4.5: class names are visible everywhere — pre-scan so casts use TYPE_ID
    # and (var) parentheses are not mistaken for casts.
    set_type_names(collect_class_names(input_text))
    lexer.lineno = 1
    ast = parser.parse(input_text, lexer=lexer)
    if ast is None:
        syntax_error = True
    return ast


def had_syntax_error():
    """Return True if the last parse() call hit a syntax error."""
    return syntax_error

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