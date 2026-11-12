"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

from typing import List, Any, Dict, Optional
from enum import Enum
from class_model import build_class_model


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
    NEW = "new"
    FIELD_GET = "field_get"
    FIELD_SET = "field_set"
    METHOD_CALL = "method_call"


class IRInstruction:
    """Represents a single IR instruction."""

    def __init__(
        self,
        ir_type: IRType,
        op: str = None,
        arg1: Any = None,
        arg2: Any = None,
        result: Any = None,
        label: str = None,
    ):
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
            return f"return {self.arg1}" if self.arg1 is not None else "return"
        elif self.type == IRType.PRINT:
            return f"print {self.arg1}"
        elif self.type == IRType.READ:
            return f"read {self.result}"
        elif self.type == IRType.NEW:
            return f"{self.result} = new {self.arg1}"
        elif self.type == IRType.FIELD_GET:
            return f"{self.result} = {self.arg1}.{self.arg2}"
        elif self.type == IRType.FIELD_SET:
            return f"{self.arg1}.{self.op} = {self.arg2}"
        elif self.type == IRType.METHOD_CALL:
            return f"{self.result} = {self.arg1}.{self.op}({self.arg2})"
        else:
            return f"Unknown instruction: {self.type}"


# Built-in function return types
_BUILTIN_RETURNS = {
    "print": "void",
    "readInt": "int",
    "readString": "string",
    "length": "int",
    "subStr": "string",
}


class IRGenerator:
    """Generates intermediate representation from AST"""

    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.var_types: Dict[str, str] = {}
        self.value_types: Dict[str, str] = {}  # temp/var name -> type

    def new_temp(self, typ: str = "int") -> str:
        self.temp_counter += 1
        name = f"t{self.temp_counter}"
        self.value_types[name] = typ
        return name

    def new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def add_instruction(self, instruction: IRInstruction):
        self.instructions.append(instruction)

    def generate_from_ast(self, ast) -> List[IRInstruction]:
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0
        self.var_types = {}
        self.value_types = {}
        self.classes = build_class_model(ast) if ast else {}
        self.func_returns = dict(_BUILTIN_RETURNS)
        if ast and ast[0] == "program":
            for definition in ast[1]:
                if definition[0] == "function":
                    self.func_returns[definition[2]] = definition[1]
        if ast:
            self._generate_node(ast)
        return self.instructions

    def _type_of(self, val: Any) -> str:
        if isinstance(val, tuple):
            if val[0] == "int_lit":
                return "int"
            if val[0] == "str_lit":
                return "string"
            if val[0] == "var":
                name = val[1]
                # Prefer declared type for locals/params so assignments from
                # mistyped temps cannot poison later string comparisons.
                if name in self.var_types:
                    return self.var_types[name]
                return self.value_types.get(name, "int")
        if isinstance(val, str):
            if val in self.var_types:
                return self.var_types[val]
            return self.value_types.get(val, "int")
        if isinstance(val, int):
            return "int"
        return "int"

    def _generate_node(self, node):
        if node is None:
            return None

        if isinstance(node, list):
            for child in node:
                self._generate_node(child)
            return None

        if not isinstance(node, tuple):
            return node

        node_type = node[0]

        if node_type == "program":
            # Emit methods first (as Class:method functions), then free functions
            for definition in node[1]:
                if definition[0] == "class":
                    self._generate_class_methods(definition)
            for definition in node[1]:
                if definition[0] == "function":
                    self._generate_node(definition)

        elif node_type == "function":
            return_type, name, params, body = node[1], node[2], node[3], node[4]
            self._emit_callable(name, return_type, params, body, is_method=False)

        elif node_type == "var_def":
            var_type, var_list = node[1], node[2]
            for name in var_list:
                self.var_types[name] = var_type
                self.value_types[name] = var_type
                if var_type == "string":
                    default = ("str_lit", "")
                else:
                    default = ("int_lit", 0)
                self.add_instruction(
                    IRInstruction(IRType.ASSIGN, arg1=default, result=name)
                )

        elif node_type == "assign":
            var_name, expr = node[1], node[2]
            expr_result = self._generate_node(expr)
            self.value_types[var_name] = self._type_of(expr_result)
            self.add_instruction(
                IRInstruction(IRType.ASSIGN, arg1=expr_result, result=var_name)
            )

        elif node_type == "field_assign":
            obj_expr, field_name, value_expr = node[1], node[2], node[3]
            obj = self._generate_node(obj_expr)
            value = self._generate_node(value_expr)
            self.add_instruction(
                IRInstruction(
                    IRType.FIELD_SET, op=field_name, arg1=obj, arg2=value
                )
            )

        elif node_type == "new":
            class_name = node[1]
            temp = self.new_temp(class_name)
            self.add_instruction(
                IRInstruction(IRType.NEW, arg1=class_name, result=temp)
            )
            return temp

        elif node_type == "this":
            return ("var", "this")

        elif node_type == "super":
            # Bare super is invalid alone; handled via method_call_expr
            return ("super",)

        elif node_type == "field_access":
            obj = self._generate_node(node[1])
            field_name = node[2]
            # Infer field type from class model when possible
            field_type = "int"
            obj_type = self._type_of(obj)
            if obj_type in self.classes:
                field_type = self.classes[obj_type].all_fields().get(field_name, "int")
            temp = self.new_temp(field_type)
            self.add_instruction(
                IRInstruction(
                    IRType.FIELD_GET, arg1=obj, arg2=field_name, result=temp
                )
            )
            return temp

        elif node_type in ("method_call", "method_call_expr"):
            # method_call: (method_call, obj, name, args) statement
            # method_call_expr: same shape
            obj_expr, method_name, args = node[1], node[2], node[3]
            is_super = isinstance(obj_expr, tuple) and obj_expr[0] == "super"
            obj = ("var", "this") if is_super else self._generate_node(obj_expr)
            arg_results = [self._generate_node(a) for a in args]
            ret_type = "int"
            # static_type = compile-time class of receiver (child class for super)
            if is_super:
                receiver_type = getattr(self, "current_class", None) or "Object"
            else:
                receiver_type = self._type_of(obj)
            lookup_type = receiver_type
            if is_super and receiver_type in self.classes:
                parent = self.classes[receiver_type].parent
                lookup_type = parent.name if parent else "Object"
            if lookup_type in self.classes:
                meth = self.classes[lookup_type].vmt().get(method_name)
                if meth:
                    ret_type = meth.return_type
            call_meta = {
                "args": arg_results,
                "super": is_super,
                "static_type": receiver_type,
            }
            if node_type == "method_call":
                self.add_instruction(
                    IRInstruction(
                        IRType.METHOD_CALL,
                        op=method_name,
                        arg1=obj,
                        arg2=call_meta,
                        result=None,
                    )
                )
                return None
            temp = self.new_temp(ret_type)
            self.add_instruction(
                IRInstruction(
                    IRType.METHOD_CALL,
                    op=method_name,
                    arg1=obj,
                    arg2=call_meta,
                    result=temp,
                )
            )
            return temp

        elif node_type == "binary":
            op, left, right = node[1], node[2], node[3]
            left_result = self._generate_node(left)
            right_result = self._generate_node(right)
            lt = self._type_of(left_result)
            rt = self._type_of(right_result)

            if op == "+" and (lt == "string" or rt == "string"):
                ir_op = "CONCAT"
                result_type = "string"
            elif op in ("==", "!=") and (lt == "string" or rt == "string"):
                ir_op = "EQS" if op == "==" else "NES"
                result_type = "int"
            elif op in ("<", ">", "<=", ">=") and (lt == "string" or rt == "string"):
                # lexicographic - map to LTS/GTS etc. in codegen via op tag
                ir_op = {"<": "LTS", ">": "GTS", "<=": "LES", ">=": "GES"}[op]
                result_type = "int"
            else:
                ir_op = op
                result_type = "int"

            temp = self.new_temp(result_type)
            self.add_instruction(
                IRInstruction(
                    IRType.BINARY_OP,
                    op=ir_op,
                    arg1=left_result,
                    arg2=right_result,
                    result=temp,
                )
            )
            return temp

        elif node_type == "unary":
            op, operand = node[1], node[2]
            operand_result = self._generate_node(operand)
            temp = self.new_temp("int")
            self.add_instruction(
                IRInstruction(
                    IRType.UNARY_OP, op=op, arg1=operand_result, result=temp
                )
            )
            return temp

        elif node_type == "int_lit":
            return ("int_lit", node[1])

        elif node_type == "str_lit":
            return ("str_lit", node[1])

        elif node_type == "var":
            return ("var", node[1])

        elif node_type == "primary":
            return node[1]

        elif node_type == "cast":
            # (type) expr
            target_type, expr = node[1], node[2]
            expr_result = self._generate_node(expr)
            temp = self.new_temp(target_type if target_type != "void" else "int")
            self.add_instruction(
                IRInstruction(
                    IRType.UNARY_OP,
                    op=f"CAST_{target_type}",
                    arg1=expr_result,
                    result=temp,
                )
            )
            return temp

        elif node_type in ("function_call", "function_call_expr"):
            func_name, args = node[1], node[2]
            arg_results = [self._generate_node(arg) for arg in args]
            if func_name == "print":
                self.add_instruction(
                    IRInstruction(
                        IRType.FUNCTION_CALL,
                        arg1=func_name,
                        arg2=arg_results,
                        result=None,
                    )
                )
                return None
            ret_type = self.func_returns.get(func_name, "int")
            temp = self.new_temp(ret_type)
            self.add_instruction(
                IRInstruction(
                    IRType.FUNCTION_CALL,
                    arg1=func_name,
                    arg2=arg_results,
                    result=temp,
                )
            )
            return temp

        elif node_type in ("if", "if_else"):
            condition_result = self._generate_node(node[1])
            else_label = self.new_label()
            end_label = self.new_label()
            self.add_instruction(
                IRInstruction(
                    IRType.CONDITIONAL_JUMP,
                    op="==",
                    arg1=condition_result,
                    arg2=("int_lit", 0),
                    label=else_label,
                )
            )
            self._generate_node(node[2])
            self.add_instruction(IRInstruction(IRType.JUMP, label=end_label))
            self.add_instruction(IRInstruction(IRType.LABEL, label=else_label))
            if node_type == "if_else":
                self._generate_node(node[3])
            self.add_instruction(IRInstruction(IRType.LABEL, label=end_label))

        elif node_type == "while":
            condition, body = node[1], node[2]
            start_label = self.new_label()
            end_label = self.new_label()
            self.add_instruction(IRInstruction(IRType.LABEL, label=start_label))
            condition_result = self._generate_node(condition)
            self.add_instruction(
                IRInstruction(
                    IRType.CONDITIONAL_JUMP,
                    op="==",
                    arg1=condition_result,
                    arg2=("int_lit", 0),
                    label=end_label,
                )
            )
            self._generate_node(body)
            self.add_instruction(IRInstruction(IRType.JUMP, label=start_label))
            self.add_instruction(IRInstruction(IRType.LABEL, label=end_label))

        elif node_type == "return":
            if node[1] is not None:
                expr_result = self._generate_node(node[1])
                self.add_instruction(
                    IRInstruction(IRType.RETURN, arg1=expr_result)
                )
            else:
                self.add_instruction(IRInstruction(IRType.RETURN))

        elif node_type == "block":
            self._generate_node(node[1])

        else:
            for child in node[1:]:
                if isinstance(child, (list, tuple)):
                    self._generate_node(child)

        return None

    def _collect_locals(self, node, found=None):
        if found is None:
            found = []
        if node is None:
            return found
        if isinstance(node, list):
            for child in node:
                self._collect_locals(child, found)
            return found
        if not isinstance(node, tuple):
            return found
        if node[0] == "var_def":
            for name in node[2]:
                if name not in found:
                    found.append(name)
        else:
            for child in node[1:]:
                if isinstance(child, (list, tuple)):
                    self._collect_locals(child, found)
        return found

    def _collect_local_types(self, node, found=None):
        if found is None:
            found = {}
        if node is None:
            return found
        if isinstance(node, list):
            for child in node:
                self._collect_local_types(child, found)
            return found
        if not isinstance(node, tuple):
            return found
        if node[0] == "var_def":
            for name in node[2]:
                found[name] = node[1]
        else:
            for child in node[1:]:
                if isinstance(child, (list, tuple)):
                    self._collect_local_types(child, found)
        return found

    def _emit_callable(self, name, return_type, params, body, is_method=False, class_name=None):
        """Emit FUNCTION_DEF + body for a function or method."""
        if is_method:
            # Hidden this parameter
            param_names = ["this"] + [p[2] for p in params]
            param_type_pairs = [("object", "this")] + [
                (p[1], p[2]) for p in params
            ]
        else:
            param_names = [p[2] for p in params]
            param_type_pairs = [(p[1], p[2]) for p in params]

        locals_list = self._collect_locals(body)
        saved_types = dict(self.value_types)
        saved_vars = dict(self.var_types)
        saved_class = getattr(self, "current_class", None)
        self.value_types = {}
        self.var_types = {}
        self.current_class = class_name
        for ptype, pname in param_type_pairs:
            # object refs use class name when known
            if pname == "this" and class_name:
                self.var_types[pname] = class_name
                self.value_types[pname] = class_name
            else:
                self.var_types[pname] = ptype
                self.value_types[pname] = ptype
        local_types = self._collect_local_types(body)
        for lname, ltype in local_types.items():
            self.var_types[lname] = ltype
            self.value_types[lname] = ltype

        self.add_instruction(
            IRInstruction(
                IRType.FUNCTION_DEF,
                arg1=name,
                arg2={
                    "return_type": return_type,
                    "params": param_names,
                    "locals": locals_list,
                    "local_types": local_types,
                    "is_method": is_method,
                    "class_name": class_name,
                },
                label=name,
            )
        )
        self._generate_node(body)
        self.value_types = saved_types
        self.var_types = saved_vars
        self.current_class = saved_class

    def _generate_class_methods(self, class_node):
        class_name = class_node[1]
        for member in class_node[3]:
            if member[0] != "method":
                continue
            ret, mname, params, body = member[1], member[2], member[3], member[4]
            label = f"{class_name}:{mname}"
            self._emit_callable(
                label, ret, params, body, is_method=True, class_name=class_name
            )
