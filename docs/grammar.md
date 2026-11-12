# VYPlanguage Grammar Specification

## Lexical Structure

### Keywords
- `class`, `else`, `if`, `int`, `new`, `return`, `string`, `super`, `this`, `void`, `while`

### Identifiers
- Start with letter or underscore
- Followed by letters, digits, or underscores
- Case sensitive
- Cannot be keywords

### Literals
- **Integer**: `123`, `456` (64-bit signed)
- **String**: `"hello world"` with escape sequences `\n`, `\t`, `\\`, `\"`

### Operators
- **Arithmetic**: `+`, `-`, `*`, `/` (integer division)
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `&&`, `||`, `!`
- **Object**: `.` (member access), `new` (object creation)

### Delimiters
- `(`, `)`, `{`, `}`, `;`, `,`, `.`, `:`

### Comments
- Line comments: `// comment`
- Block comments: `/* comment */`

## Grammar Rules

```
program ::= global_definitions

global_definitions ::= global_definitions global_definition
                    | global_definition

global_definition ::= function_definition
                   | class_definition

function_definition ::= type id '(' param_list ')' '{' statement_list '}'

class_definition ::= class id ':' id '{' class_members '}'

class_members ::= class_members class_member
                | class_member
                | empty

class_member ::= variable_definition
               | method_definition

method_definition ::= type id '(' param_list ')' '{' statement_list '}'

param_list ::= param_list ',' param
             | param
             | void
             | empty

param ::= data_type id

type ::= data_type
       | void

data_type ::= prim_type
            | id

prim_type ::= int
            | string

statement_list ::= statement_list statement
                | statement
                | empty

statement ::= variable_definition
            | assignment_statement
            | if_statement
            | while_statement
            | function_call_statement
            | method_call_statement
            | return_statement
            | block_statement

variable_definition ::= data_type variable_list ';'

variable_list ::= variable_list ',' id
                | id

assignment_statement ::= id '=' expression ';'

if_statement ::= if '(' expression ')' '{' statement_list '}' else '{' statement_list '}'

while_statement ::= while '(' expression ')' '{' statement_list '}'

function_call_statement ::= id '(' arg_list ')' ';'

method_call_statement ::= expression '.' id '(' arg_list ')' ';'

return_statement ::= return expression ';'
                  | return ';'

block_statement ::= '{' statement_list '}'

arg_list ::= arg_list ',' expression
           | expression
           | empty

expression ::= binary_expression
             | unary_expression
             | primary_expression

binary_expression ::= expression '+' expression
                    | expression '-' expression
                    | expression '*' expression
                    | expression '/' expression
                    | expression '==' expression
                    | expression '!=' expression
                    | expression '<' expression
                    | expression '>' expression
                    | expression '<=' expression
                    | expression '>=' expression
                    | expression '&&' expression
                    | expression '||' expression

unary_expression ::= '!' expression
                   | '-' expression

primary_expression ::= id
                     | integer_literal
                     | string_literal
                     | this
                     | super
                     | new id
                     | '(' type ')' expression
                     | id '(' arg_list ')'
                     | expression '.' id '(' arg_list ')'
                     | expression '.' id
                     | '(' expression ')'
```

## Precedence Rules (highest to lowest)

1. `new` (unary, right-associative)
2. `.` (left-associative)
3. `()` (function call)
4. `!` (unary, right-associative)
5. `*`, `/` (left-associative)
6. `+`, `-` (left-associative)
7. `<`, `<=`, `>`, `>=` (left-associative)
8. `==`, `!=` (left-associative)
9. `&&` (left-associative)
10. `||` (left-associative, lowest)

## Special Rules

### Main Function
Every program must contain exactly one main function:
```
void main(void) { ... }
```

### Class Inheritance
Classes can inherit from other classes:
```
class Rectangle : Shape { ... }
```

### Method Access
In method bodies, use `this.` or `super.` to access members:
```
this.field_name
super.method_name()
```

### Object Creation
Create objects using the `new` operator:
```
Rectangle r = new Rectangle;
```
