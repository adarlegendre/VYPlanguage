# Makefile for VYP Language Compiler
# Required for project evaluation

# Compiler and flags
PYTHON = python3
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2

# Directories
SRC_DIR = src
TEST_DIR = tests
DOCS_DIR = docs
BUILD_DIR = build

# Main targets
MAIN_TARGET = vypcomp
TEST_TARGETS = $(wildcard $(TEST_DIR)/*.vyp)

# Default target
all: $(MAIN_TARGET)

# Create the main compiler script
$(MAIN_TARGET): vypcomp
	chmod +x vypcomp

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Run tests
test: $(MAIN_TARGET)
	@echo "Running tests..."
	@for test in $(TEST_TARGETS); do \
		echo "Testing $$test..."; \
		./$(MAIN_TARGET) $$test -o $(BUILD_DIR)/$$(basename $$test .vyp).c; \
	done

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile a VYP file to VYPcode
%.vypcode: %.vyp $(MAIN_TARGET) | $(BUILD_DIR)
	./$(MAIN_TARGET) $< -o $@

# Run VYPcode with interpreter
%: %.vypcode
	java -jar vypint-1.0.jar $<

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	rm -f *.c *.o *.exe

# Clean everything including the compiler
distclean: clean
	rm -f $(MAIN_TARGET)

# Run a specific test
test-%: $(TEST_DIR)/%.vyp $(MAIN_TARGET) | $(BUILD_DIR)
	@echo "Testing $<..."
	./$(MAIN_TARGET) $< -o $(BUILD_DIR)/$*.vypcode
	@echo "Running $*..."
	java -jar vypint-1.0.jar $(BUILD_DIR)/$*.vypcode

# Development targets
dev-install: install
	@echo "Development environment ready"

# Check syntax of all Python files
lint:
	$(PYTHON) -m flake8 $(SRC_DIR)/*.py

# Format Python code
format:
	$(PYTHON) -m black $(SRC_DIR)/*.py

# Generate documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p $(DOCS_DIR)
	$(PYTHON) -m pydoc -w $(SRC_DIR)/*.py
	mv *.html $(DOCS_DIR)/

# Help target
help:
	@echo "Available targets:"
	@echo "  all          - Build the compiler (default)"
	@echo "  install      - Install Python dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-<name>  - Run specific test"
	@echo "  clean        - Remove build artifacts"
	@echo "  distclean    - Remove everything including compiler"
	@echo "  lint         - Check Python code style"
	@echo "  format       - Format Python code"
	@echo "  docs         - Generate documentation"
	@echo "  help         - Show this help"

# Phony targets
.PHONY: all install test clean distclean dev-install lint format docs help test-%
