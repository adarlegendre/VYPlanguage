# Testing Guide

## Test Structure

The `tests/` directory contains various test files to verify compiler functionality:

- `basic.vyp`: Basic variable declarations and expressions
- `arithmetic.vyp`: Arithmetic operations
- `control_flow.vyp`: If statements, loops
- `functions.vyp`: Function definitions and calls

## Running Tests

### All Tests
```bash
make test
```

### Individual Tests
```bash
make test-basic
make test-arithmetic
make test-control_flow
make test-functions
```

### Manual Testing

#### Lexical Analysis Only
```bash
./vypcomp tests/basic.vyp --lex-only
```

#### Syntactic Analysis Only
```bash
./vypcomp tests/basic.vyp --parse-only
```

#### Intermediate Representation
```bash
./vypcomp tests/basic.vyp --ir-only
```

#### Full Compilation
```bash
./vypcomp tests/basic.vyp -o build/basic.c
gcc build/basic.c -o build/basic
./build/basic
```

## Test Development

### Creating New Tests

1. Create a new `.vyp` file in the `tests/` directory
2. Add the test to the Makefile:
   ```makefile
   test-newfeature: $(TEST_DIR)/newfeature.vyp $(MAIN_TARGET) | $(BUILD_DIR)
   	@echo "Testing $<..."
   	./$(MAIN_TARGET) $< -o $(BUILD_DIR)/newfeature.c
   	$(CC) $(CFLAGS) $(BUILD_DIR)/newfeature.c -o $(BUILD_DIR)/newfeature
   	@echo "Running newfeature..."
   	$(BUILD_DIR)/newfeature
   ```

### Test Categories

#### Unit Tests
- Test individual components (lexer, parser, etc.)
- Verify specific functionality in isolation

#### Integration Tests
- Test multiple components working together
- Verify end-to-end compilation

#### Regression Tests
- Ensure previously fixed bugs don't reoccur
- Test edge cases and error conditions

## Expected Outputs

### Lexical Analysis
Should produce tokens with correct types and values:
```
IDENTIFIER: var (line 1)
IDENTIFIER: x (line 1)
ASSIGN: = (line 1)
INTEGER_LITERAL: 10 (line 1)
SEMICOLON: ; (line 1)
```

### Syntactic Analysis
Should produce a valid AST structure:
```
('program', [('declaration', 'var', 'x', ('primary', 10))])
```

### Intermediate Representation
Should produce three-address code:
```
  0: x = 10
  1: print x
```

### Generated C Code
Should produce compilable C code:
```c
#include <stdio.h>
#include <stdlib.h>

int main() {
    int x;
    x = 10;
    printf("%d\n", x);
    return 0;
}
```

## Debugging Tests

### Verbose Output
```bash
./vypcomp tests/basic.vyp --verbose
```

### Error Analysis
Check compiler error messages and warnings for:
- Syntax errors
- Semantic errors
- Type mismatches
- Undeclared variables

### Manual Verification
1. Compile generated C code
2. Run executable
3. Verify output matches expected behavior
4. Check for memory leaks or runtime errors



