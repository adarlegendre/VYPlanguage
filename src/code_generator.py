"""
Code Generator for VYP Language
Generates target code from intermediate representation
"""

from typing import List
from intermediate_representation import IRInstruction, IRType

class CodeGenerator:
    """Generates target code from IR"""
    
    def __init__(self):
        self.output_lines = []
        self.label_map = {}
        self.temp_map = {}
    
    def generate(self, instructions: List[IRInstruction]) -> str:
        """Generate target code from IR instructions"""
        self.output_lines = []
        self.label_map = {}
        self.temp_map = {}
        
        # First pass: collect labels and map temporaries
        self._collect_labels_and_temps(instructions)
        
        # Second pass: generate code
        for instruction in instructions:
            self._generate_instruction(instruction)
        
        return '\n'.join(self.output_lines)
    
    def _collect_labels_and_temps(self, instructions: List[IRInstruction]):
        """Collect all labels and map temporary variables"""
        temp_counter = 0
        
        for instruction in instructions:
            if instruction.type == IRType.LABEL:
                self.label_map[instruction.label] = f"label_{instruction.label}"
            
            # Map temporary variables to actual variables
            if instruction.result and instruction.result.startswith('t'):
                if instruction.result not in self.temp_map:
                    temp_counter += 1
                    self.temp_map[instruction.result] = f"temp_{temp_counter}"
    
    def _generate_instruction(self, instruction: IRInstruction):
        """Generate code for a single instruction"""
        if instruction.type == IRType.ASSIGN:
            result = self._get_var_name(instruction.result)
            arg1 = self._get_var_name(instruction.arg1)
            self.output_lines.append(f"    {result} = {arg1};")
        
        elif instruction.type == IRType.BINARY_OP:
            result = self._get_var_name(instruction.result)
            arg1 = self._get_var_name(instruction.arg1)
            arg2 = self._get_var_name(instruction.arg2)
            self.output_lines.append(f"    {result} = {arg1} {instruction.op} {arg2};")
        
        elif instruction.type == IRType.UNARY_OP:
            result = self._get_var_name(instruction.result)
            arg1 = self._get_var_name(instruction.arg1)
            self.output_lines.append(f"    {result} = {instruction.op} {arg1};")
        
        elif instruction.type == IRType.JUMP:
            label = self.label_map.get(instruction.label, instruction.label)
            self.output_lines.append(f"    goto {label};")
        
        elif instruction.type == IRType.CONDITIONAL_JUMP:
            arg1 = self._get_var_name(instruction.arg1)
            arg2 = self._get_var_name(instruction.arg2)
            label = self.label_map.get(instruction.label, instruction.label)
            self.output_lines.append(f"    if ({arg1} {instruction.op} {arg2}) goto {label};")
        
        elif instruction.type == IRType.LABEL:
            label = self.label_map.get(instruction.label, instruction.label)
            self.output_lines.append(f"{label}:")
        
        elif instruction.type == IRType.FUNCTION_CALL:
            result = self._get_var_name(instruction.result)
            func_name = instruction.arg1
            args = instruction.arg2 if instruction.arg2 else ""
            self.output_lines.append(f"    {result} = {func_name}({args});")
        
        elif instruction.type == IRType.FUNCTION_DEF:
            func_name = instruction.arg1
            self.output_lines.append(f"function {func_name}() {{")
        
        elif instruction.type == IRType.RETURN:
            if instruction.arg1:
                arg1 = self._get_var_name(instruction.arg1)
                self.output_lines.append(f"    return {arg1};")
            else:
                self.output_lines.append(f"    return;")
        
        elif instruction.type == IRType.PRINT:
            arg1 = self._get_var_name(instruction.arg1)
            self.output_lines.append(f"    print({arg1});")
        
        elif instruction.type == IRType.READ:
            result = self._get_var_name(instruction.result)
            self.output_lines.append(f"    {result} = read();")
    
    def _get_var_name(self, var):
        """Get the actual variable name, mapping temporaries if needed"""
        if var is None:
            return "null"
        elif isinstance(var, (int, float)):
            return str(var)
        elif isinstance(var, str):
            if var.startswith('t') and var in self.temp_map:
                return self.temp_map[var]
            elif var.startswith('"') and var.endswith('"'):
                return var
            else:
                return var
        else:
            return str(var)

class CCodeGenerator(CodeGenerator):
    """Generates C code from IR"""
    
    def generate(self, instructions: List[IRInstruction]) -> str:
        """Generate C code from IR instructions"""
        self.output_lines = []
        self.label_map = {}
        self.temp_map = {}
        
        # Add C header
        self.output_lines.append("#include <stdio.h>")
        self.output_lines.append("#include <stdlib.h>")
        self.output_lines.append("")
        
        # Collect labels and temporaries
        self._collect_labels_and_temps(instructions)
        
        # Declare all variables
        self._declare_variables(instructions)
        
        # Generate main function
        self.output_lines.append("int main() {")
        
        # Generate code
        for instruction in instructions:
            self._generate_instruction(instruction)
        
        self.output_lines.append("    return 0;")
        self.output_lines.append("}")
        
        return '\n'.join(self.output_lines)
    
    def _declare_variables(self, instructions: List[IRInstruction]):
        """Declare all variables used in the code"""
        variables = set()
        
        for instruction in instructions:
            if instruction.result and not instruction.result.startswith('t'):
                variables.add(instruction.result)
            if instruction.arg1 and isinstance(instruction.arg1, str) and not instruction.arg1.startswith('t'):
                variables.add(instruction.arg1)
            if instruction.arg2 and isinstance(instruction.arg2, str) and not instruction.arg2.startswith('t'):
                variables.add(instruction.arg2)
        
        # Remove string literals and numbers
        variables = {v for v in variables if not (isinstance(v, (int, float)) or (isinstance(v, str) and v.startswith('"') and v.endswith('"'))}
        
        if variables:
            var_decls = ", ".join(f"int {var}" for var in variables)
            self.output_lines.append(f"    {var_decls};")
            self.output_lines.append("")

if __name__ == "__main__":
    # Test code generation
    from intermediate_representation import IRInstruction, IRType
    
    # Sample IR instructions
    instructions = [
        IRInstruction(IRType.ASSIGN, arg1=10, result="x"),
        IRInstruction(IRType.ASSIGN, arg1=20, result="y"),
        IRInstruction(IRType.BINARY_OP, "+", "x", "y", "t1"),
        IRInstruction(IRType.PRINT, arg1="t1"),
    ]
    
    generator = CCodeGenerator()
    c_code = generator.generate(instructions)
    print("Generated C Code:")
    print(c_code)



