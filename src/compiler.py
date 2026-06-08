"""
Main Compiler Module for VYPlanguage
Coordinates all phases of compilation
"""

import sys
import os
from typing import Optional

from lexer import tokenize
from parser import parse
from symbol_table import SymbolTable
from intermediate_representation import IRGenerator
from vypcode_generator import VYPcodeGenerator

class Compiler:
    """Main compiler class that coordinates all phases"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.ir_generator = IRGenerator()
        self.vypcode_generator = VYPcodeGenerator()
        self.errors = []
        self.warnings = []
        self._add_embedded_functions()
    
    def _add_embedded_functions(self):
        """Add embedded functions to symbol table"""
        # void print(prim_type, ...)
        self.symbol_table.declare_function("print", "void")
        
        # int readInt(void)
        self.symbol_table.declare_function("readInt", "int")
        
        # string readString(void)
        self.symbol_table.declare_function("readString", "string")
        
        # int length(string)
        self.symbol_table.declare_function("length", "int", [("string", "s")])
        
        # string subStr(string, int, int)
        self.symbol_table.declare_function("subStr", "string", [
            ("string", "s"), ("int", "i"), ("int", "n")
        ])
    
    def compile(self, source_code: str, output_file: Optional[str] = None) -> bool:
        """Compile source code through all phases"""
        try:
            # Phase 1: Lexical Analysis
            print("Phase 1: Lexical Analysis...")
            tokens = tokenize(source_code)
            print(f"Generated {len(tokens)} tokens")
            
            # Phase 2: Syntactic Analysis
            print("Phase 2: Syntactic Analysis...")
            ast = parse(source_code)
            print("AST generated successfully")
            
            # Phase 3: Semantic Analysis
            print("Phase 3: Semantic Analysis...")
            self._semantic_analysis(ast)
            
            if self.errors:
                print("Semantic errors found:")
                for error in self.errors:
                    print(f"  {error}")
                return False
            
            # Phase 4: Intermediate Representation Generation
            print("Phase 4: IR Generation...")
            ir_instructions = self.ir_generator.generate_from_ast(ast)
            print(f"Generated {len(ir_instructions)} IR instructions")
            
            # Phase 5: VYPcode Generation
            print("Phase 5: VYPcode Generation...")
            target_code = self.vypcode_generator.generate(ir_instructions)
            
            # Output results
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(target_code)
                print(f"Generated VYPcode written to {output_file}")
            else:
                print("Generated VYPcode:")
                print(target_code)
            
            return True
            
        except Exception as e:
            print(f"Compilation error: {e}")
            return False
    
    def _semantic_analysis(self, ast):
        """Perform semantic analysis on the AST"""
        if not ast:
            return
        
        # Check for main function
        self._check_main_function(ast)
        
        # Process global definitions
        self._check_ast_node(ast)
    
    def _check_main_function(self, ast):
        """Check that main function exists and has correct signature"""
        if not ast or ast[0] != 'program':
            return
        
        main_found = False
        for definition in ast[1]:
            if definition[0] == 'function' and definition[2] == 'main':
                if definition[1] == 'void' and len(definition[3]) == 0:
                    main_found = True
                else:
                    self.errors.append("main function must have signature: void main(void)")
        
        if not main_found:
            self.errors.append("Program must contain exactly one main function with signature: void main(void)")
    
    def _check_ast_node(self, node):
        """Check semantic properties of an AST node"""
        if not node or not isinstance(node, tuple):
            return
        
        node_type = node[0]
        
        if node_type == 'program':
            for definition in node[1]:
                self._check_ast_node(definition)
        
        elif node_type == 'function':
            return_type, name, params, body = node[1], node[2], node[3], node[4]
            
            # Declare function in symbol table
            if not self.symbol_table.declare_function(name, return_type, params):
                self.errors.append(f"Function '{name}' already declared")
            
            # Enter function scope
            self.symbol_table.enter_scope()
            
            # Declare parameters
            for param in params:
                param_type, param_name = param[1], param[2]
                if not self.symbol_table.declare_symbol(param_name, param_type):
                    self.errors.append(f"Parameter '{param_name}' already declared")
            
            # Check function body
            self._check_ast_node(body)
            
            # Exit function scope
            self.symbol_table.exit_scope()
        
        elif node_type == 'class':
            class_name, parent_name, members = node[1], node[2], node[3]
            
            # Declare class
            if not self.symbol_table.declare_class(class_name, parent_name):
                self.errors.append(f"Class '{class_name}' already declared")
            
            # Enter class scope
            self.symbol_table.enter_class(class_name)
            
            # Process class members
            for member in members:
                self._check_ast_node(member)
            
            # Exit class scope
            self.symbol_table.exit_class()
        
        elif node_type == 'var_def':
            var_type, var_list = node[1], node[2]
            for var_name in var_list:
                if not self.symbol_table.declare_symbol(var_name, var_type):
                    self.errors.append(f"Variable '{var_name}' already declared")
        
        elif node_type == 'assign':
            var_name, expr = node[1], node[2]
            symbol = self.symbol_table.lookup_symbol(var_name)
            if not symbol:
                self.errors.append(f"Undeclared variable '{var_name}'")
            self._check_ast_node(expr)
        
        elif node_type == 'binary':
            op, left, right = node[1], node[2], node[3]
            self._check_ast_node(left)
            self._check_ast_node(right)
        
        elif node_type == 'unary':
            op, operand = node[1], node[2]
            self._check_ast_node(operand)
        
        elif node_type == 'primary':
            if isinstance(node[1], str) and not node[1].startswith('"'):
                # Check if identifier is declared
                symbol = self.symbol_table.lookup_symbol(node[1])
                if not symbol:
                    self.errors.append(f"Undeclared variable '{node[1]}'")
        
        elif node_type == 'function_call':
            func_name, args = node[1], node[2]
            function = self.symbol_table.get_function(func_name)
            if not function:
                self.errors.append(f"Undeclared function '{func_name}'")
            else:
                # Check argument count and types
                if len(args) != len(function.parameters):
                    self.errors.append(f"Function '{func_name}' expects {len(function.parameters)} arguments, got {len(args)}")
            
            for arg in args:
                self._check_ast_node(arg)
        
        elif node_type == 'if' or node_type == 'if_else':
            condition = node[1]
            self._check_ast_node(condition)
            self._check_ast_node(node[2])
            if node_type == 'if_else':
                self._check_ast_node(node[3])
        
        elif node_type == 'while':
            condition, body = node[1], node[2]
            self._check_ast_node(condition)
            self._check_ast_node(body)
        
        elif node_type == 'return':
            if node[1]:
                self._check_ast_node(node[1])
        
        elif node_type == 'block':
            self.symbol_table.enter_scope()
            for statement in node[1]:
                self._check_ast_node(statement)
            self.symbol_table.exit_scope()
        
        else:
            # Recursively check children
            for child in node[1:]:
                if isinstance(child, (list, tuple)):
                    self._check_ast_node(child)
    
    
    def get_errors(self):
        """Get compilation errors"""
        return self.errors
    
    def get_warnings(self):
        """Get compilation warnings"""
        return self.warnings

def main():
    """Main entry point for the compiler"""
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Read source code
    with open(input_file, 'r') as f:
        source_code = f.read()
    
    # Compile
    compiler = Compiler()
    success = compiler.compile(source_code, output_file)
    
    # Report errors and warnings
    if compiler.get_errors():
        print("\nErrors:")
        for error in compiler.get_errors():
            print(f"  {error}")
    
    if compiler.get_warnings():
        print("\nWarnings:")
        for warning in compiler.get_warnings():
            print(f"  {warning}")
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()