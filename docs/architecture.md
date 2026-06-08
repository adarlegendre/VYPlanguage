# Compiler Architecture

## Overview

The VYP compiler follows a traditional multi-phase architecture with the following components:

1. **Lexical Analyzer** (`lexer.py`)
2. **Syntactic Analyzer** (`parser.py`)
3. **Symbol Table** (`symbol_table.py`)
4. **Semantic Analyzer** (integrated in `compiler.py`)
5. **Intermediate Representation Generator** (`intermediate_representation.py`)
6. **Code Generator** (`code_generator.py`)

## Phase Details

### 1. Lexical Analysis
- **Tool**: PLY lex
- **Purpose**: Convert source code into tokens
- **Output**: List of tokens with type, value, and position information
- **Features**: 
  - Keyword recognition
  - Identifier and literal tokenization
  - Operator and delimiter recognition
  - Comment handling
  - Error reporting for invalid characters

### 2. Syntactic Analysis
- **Tool**: PLY yacc with LALR parsing
- **Purpose**: Build Abstract Syntax Tree (AST) from tokens
- **Output**: AST representing program structure
- **Features**:
  - Grammar rule implementation
  - Precedence and associativity handling
  - Error recovery and reporting
  - AST construction

### 3. Symbol Table Management
- **Purpose**: Track identifiers, types, and scopes
- **Features**:
  - Scope management (enter/exit scopes)
  - Symbol declaration and lookup
  - Type information storage
  - Constant vs variable distinction

### 4. Semantic Analysis
- **Purpose**: Perform type checking and semantic validation
- **Features**:
  - Variable declaration checking
  - Type compatibility validation
  - Undeclared variable detection
  - Constant modification prevention

### 5. Intermediate Representation
- **Purpose**: Generate three-address code
- **Features**:
  - Instruction-based representation
  - Temporary variable management
  - Label generation for control flow
  - Optimization opportunities

### 6. Code Generation
- **Purpose**: Generate target C code
- **Features**:
  - C code generation from IR
  - Variable declaration handling
  - Control flow translation
  - Function call translation

## Data Flow

```
Source Code → Lexer → Parser → Semantic Analyzer → IR Generator → Code Generator → C Code
                ↓         ↓           ↓              ↓              ↓
             Tokens    AST      Symbol Table    IR Instructions   Target Code
```

## Error Handling

Each phase includes comprehensive error handling:
- **Lexical**: Invalid character detection
- **Syntactic**: Grammar violation detection
- **Semantic**: Type and declaration errors
- **IR Generation**: Internal consistency checks
- **Code Generation**: Target code validation

## Extensibility

The architecture is designed for easy extension:
- New language features can be added to grammar rules
- Additional semantic checks can be integrated
- Different target languages can be supported
- Optimization passes can be added between IR and code generation



