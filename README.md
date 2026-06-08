# VYPlanguage Compiler

A compiler implementation from scratch using Python and PLY (Python Lex-Yacc) for the VYPlanguage programming language.

## Project Structure

```
VYPlanguage/
├── src/                    # Source code
│   ├── __init__.py
│   ├── lexer.py           # Lexical analyzer
│   ├── parser.py          # Syntactic analyzer
│   ├── symbol_table.py    # Symbol table management
│   ├── intermediate_representation.py  # IR generation
│   ├── code_generator.py  # Code generation
│   └── compiler.py        # Main compiler coordination
├── tests/                 # Test files
│   ├── factorial_iterative.vyp
│   ├── factorial_recursive.vyp
│   ├── string_operations.vyp
│   ├── classes_objects.vyp
│   └── simple_arithmetic.vyp
├── docs/                  # Documentation
├── build/                 # Build output
├── vypcomp               # Main compiler script
├── Makefile              # Build configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Features

- **Lexical Analysis**: Tokenization using PLY lex with VYPlanguage keywords and operators
- **Syntactic Analysis**: LALR parsing using PLY yacc with complete VYPlanguage grammar
- **Semantic Analysis**: Symbol table management, type checking, and class support
- **Intermediate Representation**: Three-address code generation
- **Code Generation**: C code output
- **Error Handling**: Comprehensive error reporting

## VYPlanguage Features

### Data Types
- `int`: 64-bit signed integers
- `string`: UTF-8 strings with escape sequences
- `void`: No value type for functions
- User-defined classes (object types)

### Keywords
- `class`, `else`, `if`, `int`, `new`, `return`, `string`, `super`, `this`, `void`, `while`

### Variables and Functions
```vyp
int a, b, c;
string str1, str2;

void main(void) {
    a = 10;
    b = 20;
    c = a + b;
}
```

### Classes and Objects
```vyp
class Shape : Object {
    int id;
    void Shape(void) { print("constructor of Shape"); }
    string toString(void) { return "instance of Shape " + (string)this.id; }
}

class Rectangle : Shape {
    int height, width;
    int area(void) { return this.height * this.width; }
}
```

### Embedded Functions
- `void print(prim_type, ...)` - Print values to stdout
- `int readInt(void)` - Read integer from stdin
- `string readString(void)` - Read string from stdin
- `int length(string)` - Get string length
- `string subStr(string, int, int)` - Extract substring

### Operators
- **Arithmetic**: `+`, `-`, `*`, `/` (integer division)
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `&&`, `||`, `!`
- **Object**: `.` (member access), `new` (object creation)

## Installation

1. Install Python dependencies:
```bash
make install
```

2. Build the compiler:
```bash
make
```

## Usage

### Basic Usage
```bash
./vypcomp input.vyp -o output.c
```

### Command Line Options
- `-o, --output`: Specify output file
- `--lex-only`: Perform only lexical analysis
- `--parse-only`: Perform lexical and syntactic analysis
- `--ir-only`: Generate intermediate representation only
- `--verbose, -v`: Verbose output

### Examples

#### Lexical Analysis Only
```bash
./vypcomp tests/simple_arithmetic.vyp --lex-only
```

#### Generate C Code
```bash
./vypcomp tests/factorial_iterative.vyp -o factorial.c
gcc factorial.c -o factorial
./factorial
```

## Testing

Run all tests:
```bash
make test
```

Run specific test:
```bash
make test-factorial_iterative
```

## Development

### Code Style
```bash
make lint      # Check code style
make format    # Format code
```

### Documentation
```bash
make docs      # Generate documentation
```

## Compilation Phases

1. **Lexical Analysis**: Tokenizes input into tokens with proper keyword recognition
2. **Syntactic Analysis**: Builds Abstract Syntax Tree (AST) using VYPlanguage grammar
3. **Semantic Analysis**: Type checking, symbol table management, and class validation
4. **Intermediate Representation**: Generates three-address code
5. **Code Generation**: Produces target C code

## Error Handling

The compiler provides detailed error messages for:
- Lexical errors (invalid characters, malformed strings)
- Syntax errors (grammar violations)
- Semantic errors (undeclared variables, type mismatches, missing main function)

## Requirements

- Python 3.7+
- PLY (Python Lex-Yacc)
- GCC (for compiling generated C code)

## Language Specification

VYPlanguage is inspired by C and Java with the following characteristics:
- Case-sensitive language
- Typed language with int and string primitive types
- Object-oriented with classes and inheritance
- Supports recursive function calls
- Main function entry point: `void main(void)`
- Line comments (`//`) and block comments (`/* */`)

## License

This project is part of a compiler design course assignment.
