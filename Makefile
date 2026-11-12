# Makefile for VYP Language Compiler (VYPa project)
# Authors: replace xlogin01 / xlogin02 in division and source headers

PYTHON = python3

SRC_DIR = src
TEST_DIR = tests
BUILD_DIR = build
MAIN_TARGET = vypcomp

.PHONY: all install test clean distclean help test-%

# Default: ensure compiler script is executable
all: $(MAIN_TARGET)

$(MAIN_TARGET): vypcomp
	chmod +x vypcomp

install:
	$(PYTHON) -m pip install -r requirements.txt

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile all valid-looking tests (positional CLI: INPUT [OUTPUT])
test: $(MAIN_TARGET) | $(BUILD_DIR)
	@echo "Running compile tests..."
	@for test in $(TEST_DIR)/simple_arithmetic.vyp \
	             $(TEST_DIR)/factorial_iterative.vyp \
	             $(TEST_DIR)/factorial_recursive.vyp \
	             $(TEST_DIR)/string_operations.vyp \
	             $(TEST_DIR)/classes_objects.vyp \
	             $(TEST_DIR)/functions.vyp; do \
		if [ -f "$$test" ]; then \
			echo "Compiling $$test..."; \
			./$(MAIN_TARGET) $$test $(BUILD_DIR)/$$(basename $$test .vyp).vc || exit $$?; \
		fi; \
	done
	@echo "All compile tests OK."

# Compile + interpret a named test: make test-simple_arithmetic
test-%: $(TEST_DIR)/%.vyp $(MAIN_TARGET) | $(BUILD_DIR)
	./$(MAIN_TARGET) $< $(BUILD_DIR)/$*.vc
	java -jar vypint-1.0.jar $(BUILD_DIR)/$*.vc

clean:
	rm -rf $(BUILD_DIR)
	rm -f out.vc *.vc
	rm -f $(SRC_DIR)/parser.out $(SRC_DIR)/parsetab.py
	rm -rf $(SRC_DIR)/__pycache__

distclean: clean

help:
	@echo "Targets:"
	@echo "  all / make     - prepare vypcomp"
	@echo "  install        - pip install -r requirements.txt"
	@echo "  test           - compile core test programs"
	@echo "  test-<name>    - compile and run tests/<name>.vyp with vypint"
	@echo "  clean          - remove build artifacts"
