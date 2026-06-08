"""
Intermediate Representation for VYP Language
Three-address code representation
"""

from typing import List, Any, Optional
from enum import Enum

class IRType(Enum):
    """Types of IR instructions"""
    ASSIGN = "assign"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    JUMP = "jump"
    CONDITIONAL_JUMP = "conditional_jump"
    LABEL = "label"
    FUNCTION_CALL = "function_call"
    FUNCTION_DEF = "function_def"
    RETURN = "return"
    PRINT = "print"
    READ = "read"

class IRInstruction:
    """Represents a single IR instruction"""
    
    def __init__(self, ir_type: IRType, op: str = None, 
                 arg1: Any = None, arg2: Any = None, result: Any = None, label: str = None):
        self.type = ir_type
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.label = label
    
    def __repr__(self):
        if self.type == IRType.ASSIGN:
            return f"{self.result} = {self.arg1}"
        elif self.type == IRType.BINARY_OP:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.type == IRType.UNARY_OP:
            return f"{self.result} = {self.op} {self.arg1}"
        elif self.type == IRType.JUMP:
            return f"goto {self.label}"
        elif self.type == IRType.CONDITIONAL_JUMP:
            return f"if {self.arg1} {self.op} {self.arg2} goto {self.label}"
        elif self.type == IRType.LABEL:
            return f"{self.label}:"
        elif self.type == IRType.FUNCTION_CALL:
            return f"{self.result} = call {self.arg1}({self.arg2})"
        elif self.type == IRType.FUNCTION_DEF:
            return f"function {self.arg1}()"
        elif self.type == IRType.RETURN:
            return f"return {self.arg1}" if self.arg1 else "return"
        elif self.type == IRType.PRINT:
            return f"print {self.arg1}"
        elif self.type == IRType.READ:
            return f"read {self.result}"
        else:
            return f"Unknown instruction: {self.type}"

class IRGenerator:
    """Generates intermediate representation from AST"""
    
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
    
    def new_temp(self) -> str:
        """Generate a new temporary variable"""
        self.temp_counter += 1
        return f"t{self.temp_counter}"
    
    def new_label(self) -> str:
        """Generate a new label"""
        self.label_counter += 1
        return f"L{self.label_counter}"
    
    def add_instruction(self, instruction: IRInstruction):
        """Add an instruction to the IR"""
        self.instructions.append(instruction)
    
    def generate_from_ast(self, ast) -> List[IRInstruction]:
        """Generate IR from AST"""
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        
        if ast:
            self._generate_node(ast)
        
        return self.instructions
    
    def _generate_node(self, node):
        """Generate IR for a specific AST node"""
        if not node or not isinstance(node, tuple):
            return node
        
        node_type = node[0]
        
        if node_type == 'program':
            for definition in node[1]:
                self._generate_node(definition)
        
        elif node_type == 'function':
            return_type, name, params, body = node[1], node[2], node[3], node[4]
            
            # Generate function label
            if name == 'main':
                self.add_instruction(IRInstruction(IRType.LABEL, label='main'))
            
            # Generate function body (which is a block)
            if isinstance(body, list):
                for statement in body:
                    self._generate_node(statement)
            else:
                self._generate_node(body)
        
        elif node_type == 'var_def':
            var_type, var_list = node[1], node[2]
            # Variable declarations don't generate IR instructions in this simple implementation
            # They are handled by the symbol table
        
        elif node_type == 'assign':
            var_name, expr = node[1], node[2]
            expr_result = self._generate_node(expr)
            self.add_instruction(IRInstruction(IRType.ASSIGN, arg1=expr_result, result=var_name))
        
        elif node_type == 'binary':
            op, left, right = node[1], node[2], node[3]
            left_result = self._generate_node(left)
            right_result = self._generate_node(right)
            temp = self.new_temp()
            self.add_instruction(IRInstruction(IRType.BINARY_OP, op, left_result, right_result, temp))
            return temp
        
        elif node_type == 'unary':
            op, operand = node[1], node[2]
            operand_result = self._generate_node(operand)
            temp = self.new_temp()
            self.add_instruction(IRInstruction(IRType.UNARY_OP, op, operand_result, result=temp))
            return temp
        
        elif node_type == 'primary':
            return node[1]
        
        elif node_type == 'function_call':
            func_name, args = node[1], node[2]
            arg_results = []
            for arg in args:
                arg_result = self._generate_node(arg)
                arg_results.append(arg_result)
            
            temp = self.new_temp()
            self.add_instruction(IRInstruction(IRType.FUNCTION_CALL, func_name, arg_results, temp))
            return temp
        
        elif node_type == 'function_call_expr':
            func_name, args = node[1], node[2]
            arg_results = []
            for arg in args:
                arg_result = self._generate_node(arg)
                arg_results.append(arg_result)
            
            temp = self.new_temp()
            self.add_instruction(IRInstruction(IRType.FUNCTION_CALL, func_name, arg_results, temp))
            return temp
        
        elif node_type == 'if' or node_type == 'if_else':
            condition = node[1]
            condition_result = self._generate_node(condition)
            else_label = self.new_label()
            end_label = self.new_label()
            
            self.add_instruction(IRInstruction(IRType.CONDITIONAL_JUMP, "==", condition_result, "0", else_label))
            self._generate_node(node[2])
            self.add_instruction(IRInstruction(IRType.JUMP, label=end_label))
            self.add_instruction(IRInstruction(IRType.LABEL, label=else_label))
            if node_type == 'if_else':
                self._generate_node(node[3])
            self.add_instruction(IRInstruction(IRType.LABEL, label=end_label))
        
        elif node_type == 'while':
            condition, body = node[1], node[2]
            start_label = self.new_label()
            end_label = self.new_label()
            
            self.add_instruction(IRInstruction(IRType.LABEL, label=start_label))
            condition_result = self._generate_node(condition)
            self.add_instruction(IRInstruction(IRType.CONDITIONAL_JUMP, "==", condition_result, "0", end_label))
            self._generate_node(body)
            self.add_instruction(IRInstruction(IRType.JUMP, label=start_label))
            self.add_instruction(IRInstruction(IRType.LABEL, label=end_label))
        
        elif node_type == 'return':
            if node[1]:
                expr_result = self._generate_node(node[1])
                self.add_instruction(IRInstruction(IRType.RETURN, arg1=expr_result))
            else:
                self.add_instruction(IRInstruction(IRType.RETURN))
        
        elif node_type == 'block':
            for statement in node[1]:
                self._generate_node(statement)
        
        else:
            # For other node types, recursively process children
            for child in node[1:]:
                if isinstance(child, (list, tuple)):
                    self._generate_node(child)
                else:
                    return child

if __name__ == "__main__":
    # Test IR generation
    from parser import parse
    
    test_code = """
    var x = 10;
    var y = 20;
    if (x > y) {
        print("x is greater");
    } else {
        print("y is greater");
    }
    """
    
    ast = parse(test_code)
    ir_gen = IRGenerator()
    ir_instructions = ir_gen.generate_from_ast(ast)
    
    print("Generated IR Instructions:")
    for i, instruction in enumerate(ir_instructions):
        print(f"{i:3d}: {instruction}")
