"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

import sys
import os
from typing import Optional, List, Tuple

from lexer import tokenize, had_lexical_error
from parser import parse, had_syntax_error
from symbol_table import SymbolTable
from intermediate_representation import IRGenerator
from vypcode_generator import VYPcodeGenerator
from class_model import build_class_model
from errors import (
    EXIT_OK,
    EXIT_LEXICAL,
    EXIT_SYNTAX,
    EXIT_SEMANTIC_TYPE,
    EXIT_SEMANTIC,
    EXIT_CODEGEN,
    EXIT_INTERNAL,
)


PRIM_TYPES = {"int", "string"}


class Compiler:
    """Main compiler class that coordinates all phases"""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.ir_generator = IRGenerator()
        self.vypcode_generator = VYPcodeGenerator()
        self.errors: List[Tuple[int, str]] = []
        self.warnings: List[str] = []
        self._current_return_type: Optional[str] = None
        self._in_method = False
        self._current_class: Optional[str] = None
        # Fields of the current class visible via this.field (§4.5 textual scope)
        self._method_visible_fields: Optional[set] = None
        self._add_embedded_functions()

    def _add_embedded_functions(self):
        """Add embedded functions to symbol table"""
        self.symbol_table.declare_function("print", "void", [])
        self.symbol_table.declare_function("readInt", "int", [])
        self.symbol_table.declare_function("readString", "string", [])
        self.symbol_table.declare_function("length", "int", [("string", "s")])
        self.symbol_table.declare_function(
            "subStr",
            "string",
            [("string", "s"), ("int", "i"), ("int", "n")],
        )

    def _semantic_error(self, message: str, code: int = EXIT_SEMANTIC):
        self.errors.append((code, message))

    @staticmethod
    def _normalize_params(params) -> List[Tuple[str, str]]:
        result = []
        for p in params or []:
            if isinstance(p, tuple) and len(p) >= 3 and p[0] == "param":
                result.append((p[1], p[2]))
            elif isinstance(p, tuple) and len(p) == 2:
                result.append((p[0], p[1]))
        return result

    def compile(self, source_code: str, output_file: Optional[str] = None) -> int:
        """Compile source code through all phases.

        Returns a VYPa specification exit code (0, 11–15, 19).
        Writes nothing to stdout. Error messages go to stderr.
        """
        try:
            tokenize(source_code)
            if had_lexical_error():
                return EXIT_LEXICAL

            ast = parse(source_code)
            if had_syntax_error() or ast is None:
                return EXIT_SYNTAX

            self._semantic_analysis(ast)
            if self.errors:
                for _code, message in self.errors:
                    print(message, file=sys.stderr)
                if any(code == EXIT_SEMANTIC_TYPE for code, _ in self.errors):
                    return EXIT_SEMANTIC_TYPE
                return EXIT_SEMANTIC

            ir_instructions = self.ir_generator.generate_from_ast(ast)
            classes = build_class_model(ast)

            try:
                target_code = self.vypcode_generator.generate(
                    ir_instructions, classes=classes
                )
            except Exception as e:
                print(f"Code generation error: {e}", file=sys.stderr)
                return EXIT_CODEGEN

            if output_file:
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(target_code)
                except OSError as e:
                    print(f"Failed to write output file: {e}", file=sys.stderr)
                    return EXIT_INTERNAL

            return EXIT_OK

        except Exception as e:
            print(f"Internal compiler error: {e}", file=sys.stderr)
            return EXIT_INTERNAL

    def _semantic_analysis(self, ast):
        """Two-pass semantic analysis (§4.2 forward refs)."""
        if not ast:
            return

        self._current_return_type = None
        self._in_method = False
        self._current_class = None
        self._method_visible_fields = None

        self._check_main_function(ast)
        self._declare_globals(ast)
        self._register_class_members(ast)
        self._validate_inheritance()
        self._check_ast_node(ast)

    def _declare_globals(self, ast):
        if not ast or ast[0] != "program":
            return
        for definition in ast[1]:
            if definition[0] == "function":
                return_type, name, params, _body = (
                    definition[1],
                    definition[2],
                    definition[3],
                    definition[4],
                )
                norm = self._normalize_params(params)
                if not self.symbol_table.declare_function(name, return_type, norm):
                    self._semantic_error(f"Function '{name}' already declared")
            elif definition[0] == "class":
                class_name, parent_name, _members = (
                    definition[1],
                    definition[2],
                    definition[3],
                )
                if not self.symbol_table.declare_class(class_name, parent_name):
                    self._semantic_error(f"Class '{class_name}' already declared")

    def _register_class_members(self, ast):
        if not ast or ast[0] != "program":
            return
        for definition in ast[1]:
            if definition[0] != "class":
                continue
            class_name, _parent, members = definition[1], definition[2], definition[3]
            self.symbol_table.enter_class(class_name)
            class_info = self.symbol_table.get_class(class_name)

            # Pass A: fields
            for member in members:
                if member[0] != "var_def":
                    continue
                ftype, names = member[1], member[2]
                if not self._is_valid_data_type(ftype):
                    self._semantic_error(
                        f"Unknown type '{ftype}' for field in class '{class_name}'"
                    )
                    continue
                for fname in names:
                    if self.symbol_table.lookup_field(class_name, fname):
                        self._semantic_error(
                            f"Field '{fname}' redefines an inherited or "
                            f"existing field in class '{class_name}'"
                        )
                        continue
                    self.symbol_table.add_class_field(fname, ftype)

            # Pass B: methods
            for member in members:
                if member[0] != "method":
                    continue
                ret, mname, params, _body = (
                    member[1],
                    member[2],
                    member[3],
                    member[4],
                )
                norm = self._normalize_params(params)
                if not self._is_valid_type(ret):
                    self._semantic_error(
                        f"Unknown return type '{ret}' for method '{mname}'"
                    )
                for ptype, _pname in norm:
                    if not self._is_valid_data_type(ptype):
                        self._semantic_error(
                            f"Unknown parameter type '{ptype}' in method '{mname}'"
                        )
                if mname == class_name:
                    if ret != "void" or len(norm) != 0:
                        self._semantic_error(
                            f"Constructor '{mname}' must be void with no parameters"
                        )
                    self.symbol_table.add_class_constructor(mname, norm)
                parent_method = None
                if class_info and class_info.parent:
                    parent_method = self.symbol_table.lookup_method(
                        class_info.parent, mname
                    )
                if parent_method:
                    parent_params = self._normalize_params(parent_method.parameters)
                    if parent_method.return_type != ret or parent_params != norm:
                        self._semantic_error(
                            f"Method '{mname}' override has incompatible "
                            f"signature in class '{class_name}'",
                            EXIT_SEMANTIC_TYPE,
                        )
                if class_info and class_info.get_field(mname):
                    self._semantic_error(
                        f"Method '{mname}' conflicts with a field in "
                        f"class '{class_name}'"
                    )
                elif (
                    class_info
                    and class_info.parent
                    and self.symbol_table.lookup_field(class_info.parent, mname)
                ):
                    self._semantic_error(
                        f"Method '{mname}' conflicts with an inherited field "
                        f"in class '{class_name}'"
                    )
                if class_info and class_info.get_method(mname):
                    self._semantic_error(
                        f"Method '{mname}' already declared in class '{class_name}'"
                    )
                else:
                    self.symbol_table.add_class_method(mname, ret, norm)

            # Field vs method name clashes (same class + inherited methods)
            if class_info:
                for fname in list(class_info.fields.keys()):
                    if class_info.get_method(fname):
                        self._semantic_error(
                            f"Field '{fname}' conflicts with a method in "
                            f"class '{class_name}'"
                        )
                    elif class_info.parent and self.symbol_table.lookup_method(
                        class_info.parent, fname
                    ):
                        self._semantic_error(
                            f"Field '{fname}' conflicts with an inherited method "
                            f"in class '{class_name}'"
                        )
            self.symbol_table.exit_class()

    def _validate_inheritance(self):
        for name, info in list(self.symbol_table.classes.items()):
            if name == "Object":
                continue
            parent = info.parent
            if parent is None or self.symbol_table.get_class(parent) is None:
                self._semantic_error(
                    f"Class '{name}' has unknown parent '{parent}'"
                )
                continue
            # Cycle detection
            seen = set()
            current = parent
            while current:
                if current == name:
                    self._semantic_error(
                        f"Inheritance cycle detected involving class '{name}'"
                    )
                    break
                if current in seen:
                    break
                seen.add(current)
                parent_info = self.symbol_table.get_class(current)
                if not parent_info:
                    break
                current = parent_info.parent

    def _check_main_function(self, ast):
        if not ast or ast[0] != "program":
            return

        main_found = False
        for definition in ast[1]:
            if definition[0] == "function" and definition[2] == "main":
                if definition[1] == "void" and len(definition[3]) == 0:
                    main_found = True
                else:
                    self._semantic_error(
                        "main function must have signature: void main(void)"
                    )

        if not main_found:
            self._semantic_error(
                "Program must contain exactly one main function with signature: "
                "void main(void)"
            )

    def _is_valid_data_type(self, type_name: str) -> bool:
        return type_name in PRIM_TYPES or self.symbol_table.is_class_type(type_name)

    def _is_valid_type(self, type_name: str) -> bool:
        return type_name == "void" or self._is_valid_data_type(type_name)

    def _types_compatible(self, expected: str, actual: Optional[str]) -> bool:
        if actual is None or expected is None:
            return False
        if expected == actual:
            return True
        if self.symbol_table.is_class_type(expected) and self.symbol_table.is_class_type(
            actual
        ):
            return self.symbol_table.is_subclass(actual, expected)
        return False

    @staticmethod
    def _is_this_or_super_member(node) -> bool:
        """True for this.x / super.x / this.m() / super.m() (one member level)."""
        if not isinstance(node, tuple):
            return False
        if node[0] not in ("field_access", "method_call", "method_call_expr"):
            return False
        obj = node[1]
        return isinstance(obj, tuple) and obj[0] in ("this", "super")

    def _reject_this_super_cascade(self, obj_expr) -> bool:
        """Spec §4.5: cannot cascade after this/super (only one member id)."""
        if self._is_this_or_super_member(obj_expr):
            self._semantic_error(
                "Cannot cascade member access after 'this' or 'super'"
            )
            return True
        return False

    def _lookup_field_access(self, obj_expr, obj_t: str, field_name: str):
        """Resolve field; this.field obeys textual definition order (§4.5)."""
        is_this = isinstance(obj_expr, tuple) and obj_expr[0] == "this"
        if (
            is_this
            and self._method_visible_fields is not None
            and obj_t == self._current_class
        ):
            info = self.symbol_table.get_class(obj_t)
            if info and info.parent:
                inherited = self.symbol_table.lookup_field(info.parent, field_name)
                if inherited:
                    return inherited
            if field_name not in self._method_visible_fields:
                return None
            return info.get_field(field_name) if info else None
        return self.symbol_table.lookup_field(obj_t, field_name)

    def _check_scoped_statements(self, statements):
        """Enter a block namespace for a statement list (§4.6)."""
        self.symbol_table.enter_scope()
        self._check_ast_node(statements)
        self.symbol_table.exit_scope()

    def _expr_type(self, node) -> Optional[str]:
        """Infer expression type; may record semantic errors as a side effect."""
        if node is None:
            return None
        if not isinstance(node, tuple):
            return None

        kind = node[0]

        if kind == "int_lit":
            return "int"
        if kind == "str_lit":
            return "string"
        if kind == "this":
            if not self._in_method or not self._current_class:
                self._semantic_error("'this' used outside of a method")
                return None
            return self._current_class
        if kind == "super":
            if not self._in_method or not self._current_class:
                self._semantic_error("'super' used outside of a method")
                return None
            info = self.symbol_table.get_class(self._current_class)
            if not info or not info.parent:
                self._semantic_error("'super' has no parent class")
                return None
            return info.parent
        if kind == "var":
            name = node[1]
            symbol = self.symbol_table.lookup_symbol(name)
            if not symbol:
                self._semantic_error(f"Undeclared variable '{name}'")
                return None
            return symbol.type
        if kind == "primary":
            value = node[1]
            if isinstance(value, tuple):
                return self._expr_type(value)
            if isinstance(value, str) and value.isidentifier():
                return self._expr_type(("var", value))
            return None
        if kind == "new":
            class_name = node[1]
            if not self.symbol_table.get_class(class_name):
                self._semantic_error(f"Unknown class '{class_name}' in new")
                return None
            return class_name
        if kind == "cast":
            target, expr = node[1], node[2]
            src = self._expr_type(expr)
            if not self._is_valid_data_type(target):
                self._semantic_error(f"Invalid cast target type '{target}'")
                return None
            if target == "string" and src == "int":
                return "string"
            if (
                src
                and self.symbol_table.is_class_type(target)
                and self.symbol_table.is_class_type(src)
            ):
                if self.symbol_table.is_subclass(
                    src, target
                ) or self.symbol_table.is_subclass(target, src):
                    return target
                self._semantic_error(
                    f"Incompatible object cast from '{src}' to '{target}'",
                    EXIT_SEMANTIC_TYPE,
                )
                return None
            self._semantic_error(
                f"Invalid cast from '{src}' to '{target}'",
                EXIT_SEMANTIC_TYPE,
            )
            return None
        if kind == "unary":
            op, operand = node[1], node[2]
            ot = self._expr_type(operand)
            if op == "!":
                if ot == "int" or (ot and self.symbol_table.is_class_type(ot)):
                    return "int"
                self._semantic_error(
                    f"Unary '!' requires int or object, got '{ot}'",
                    EXIT_SEMANTIC_TYPE,
                )
                return None
            self._semantic_error(f"Unsupported unary operator '{op}'")
            return None
        if kind == "binary":
            return self._binary_type(node[1], node[2], node[3])
        if kind == "field_access":
            if self._reject_this_super_cascade(node[1]):
                self._expr_type(node[1])
                return None
            obj_expr = node[1]
            obj_t = self._expr_type(obj_expr)
            field_name = node[2]
            if not obj_t or not self.symbol_table.is_class_type(obj_t):
                self._semantic_error(
                    f"Field access on non-object type '{obj_t}'",
                    EXIT_SEMANTIC_TYPE,
                )
                return None
            field = self._lookup_field_access(obj_expr, obj_t, field_name)
            if not field:
                self._semantic_error(
                    f"Unknown field '{field_name}' on type '{obj_t}'"
                )
                return None
            return field.type
        if kind in ("method_call", "method_call_expr"):
            return self._check_method_call(node)
        if kind in ("function_call", "function_call_expr"):
            return self._check_function_call(node)
        return None

    def _binary_type(self, op: str, left, right) -> Optional[str]:
        lt = self._expr_type(left)
        rt = self._expr_type(right)
        if lt is None or rt is None:
            return None

        if op == "+":
            if lt == "int" and rt == "int":
                return "int"
            if lt == "string" and rt == "string":
                return "string"
            self._semantic_error(
                f"Operator '+' requires int+int or string+string, got '{lt}' and '{rt}'",
                EXIT_SEMANTIC_TYPE,
            )
            return None

        if op in ("-", "*", "/"):
            if lt == "int" and rt == "int":
                return "int"
            self._semantic_error(
                f"Operator '{op}' requires int operands, got '{lt}' and '{rt}'",
                EXIT_SEMANTIC_TYPE,
            )
            return None

        if op in ("<", ">", "<=", ">="):
            if lt == rt and lt in PRIM_TYPES:
                return "int"
            self._semantic_error(
                f"Relational operator '{op}' requires matching primitive types, "
                f"got '{lt}' and '{rt}'",
                EXIT_SEMANTIC_TYPE,
            )
            return None

        if op in ("==", "!="):
            if lt == rt:
                return "int"
            if self.symbol_table.is_class_type(lt) and self.symbol_table.is_class_type(
                rt
            ):
                if self.symbol_table.is_subclass(
                    lt, rt
                ) or self.symbol_table.is_subclass(rt, lt):
                    return "int"
            self._semantic_error(
                f"Comparison '{op}' requires compatible types, got '{lt}' and '{rt}'",
                EXIT_SEMANTIC_TYPE,
            )
            return None

        if op in ("&&", "||"):
            def is_nc(t):
                return t == "int" or self.symbol_table.is_class_type(t)

            if is_nc(lt) and is_nc(rt):
                return "int"
            self._semantic_error(
                f"Logical operator '{op}' requires int/object operands, "
                f"got '{lt}' and '{rt}'",
                EXIT_SEMANTIC_TYPE,
            )
            return None

        self._semantic_error(f"Unsupported binary operator '{op}'")
        return None

    def _check_function_call(self, node) -> Optional[str]:
        func_name, args = node[1], node[2]
        function = self.symbol_table.get_function(func_name)
        if not function:
            self._semantic_error(f"Undeclared function '{func_name}'")
            for arg in args:
                self._expr_type(arg)
            return None

        if func_name == "print":
            if len(args) < 1:
                self._semantic_error(
                    "Function 'print' expects at least one argument",
                    EXIT_SEMANTIC_TYPE,
                )
            for arg in args:
                at = self._expr_type(arg)
                if at not in PRIM_TYPES:
                    self._semantic_error(
                        f"print expects primitive arguments, got '{at}'",
                        EXIT_SEMANTIC_TYPE,
                    )
            return "void"

        params = self._normalize_params(function.parameters)
        if len(args) != len(params):
            self._semantic_error(
                f"Function '{func_name}' expects {len(params)} arguments, "
                f"got {len(args)}",
                EXIT_SEMANTIC_TYPE,
            )
        for arg, (ptype, _pname) in zip(args, params):
            at = self._expr_type(arg)
            if not self._types_compatible(ptype, at):
                self._semantic_error(
                    f"Argument type '{at}' incompatible with parameter type "
                    f"'{ptype}' in call to '{func_name}'",
                    EXIT_SEMANTIC_TYPE,
                )
        # Still type-check leftover args if arity mismatch
        for arg in args[len(params) :]:
            self._expr_type(arg)
        return function.return_type

    def _check_method_call(self, node) -> Optional[str]:
        obj_expr, method_name, args = node[1], node[2], node[3]
        if self._reject_this_super_cascade(obj_expr):
            for arg in args:
                self._expr_type(arg)
            return None
        is_super = isinstance(obj_expr, tuple) and obj_expr[0] == "super"

        if is_super:
            if not self._in_method or not self._current_class:
                self._semantic_error("'super' used outside of a method")
                receiver = None
            else:
                info = self.symbol_table.get_class(self._current_class)
                receiver = info.parent if info else None
                if not receiver:
                    self._semantic_error(
                        f"Class '{self._current_class}' has no parent for super"
                    )
        else:
            receiver = self._expr_type(obj_expr)

        if not receiver or not self.symbol_table.is_class_type(receiver):
            if receiver is not None:
                self._semantic_error(
                    f"Method call on non-object type '{receiver}'",
                    EXIT_SEMANTIC_TYPE,
                )
            for arg in args:
                self._expr_type(arg)
            return None

        method = self.symbol_table.lookup_method(receiver, method_name)
        if not method:
            self._semantic_error(
                f"Unknown method '{method_name}' on type '{receiver}'"
            )
            for arg in args:
                self._expr_type(arg)
            return None

        params = self._normalize_params(method.parameters)
        if len(args) != len(params):
            self._semantic_error(
                f"Method '{method_name}' expects {len(params)} arguments, "
                f"got {len(args)}",
                EXIT_SEMANTIC_TYPE,
            )
        for arg, (ptype, _pname) in zip(args, params):
            at = self._expr_type(arg)
            if not self._types_compatible(ptype, at):
                self._semantic_error(
                    f"Argument type '{at}' incompatible with parameter type "
                    f"'{ptype}' in call to '{method_name}'",
                    EXIT_SEMANTIC_TYPE,
                )
        for arg in args[len(params) :]:
            self._expr_type(arg)
        return method.return_type

    def _check_condition(self, expr, context: str):
        ct = self._expr_type(expr)
        if ct == "int" or (ct and self.symbol_table.is_class_type(ct)):
            return
        self._semantic_error(
            f"{context} condition must be int or object, got '{ct}'",
            EXIT_SEMANTIC_TYPE,
        )

    def _declare_local(self, var_name: str, var_type: str):
        if not self._is_valid_data_type(var_type):
            self._semantic_error(f"Unknown type '{var_type}' for variable '{var_name}'")
            return
        if self.symbol_table.get_function(var_name) or self.symbol_table.get_class(
            var_name
        ):
            self._semantic_error(
                f"Variable '{var_name}' conflicts with a function or class name"
            )
            return
        if not self.symbol_table.declare_symbol(var_name, var_type):
            self._semantic_error(f"Variable '{var_name}' already declared")

    def _check_ast_node(self, node):
        if node is None:
            return

        if isinstance(node, list):
            for child in node:
                self._check_ast_node(child)
            return

        if not isinstance(node, tuple):
            return

        node_type = node[0]

        if node_type == "program":
            for definition in node[1]:
                self._check_ast_node(definition)

        elif node_type == "function":
            return_type, _name, params, body = node[1], node[2], node[3], node[4]
            if not self._is_valid_type(return_type):
                self._semantic_error(f"Unknown return type '{return_type}'")
            self.symbol_table.enter_scope()
            prev_ret, prev_method, prev_class = (
                self._current_return_type,
                self._in_method,
                self._current_class,
            )
            self._current_return_type = return_type
            self._in_method = False
            self._current_class = None
            for ptype, pname in self._normalize_params(params):
                if not self._is_valid_data_type(ptype):
                    self._semantic_error(
                        f"Unknown parameter type '{ptype}' for '{pname}'"
                    )
                elif not self.symbol_table.declare_symbol(pname, ptype):
                    self._semantic_error(f"Parameter '{pname}' already declared")
            self._check_ast_node(body)
            self._current_return_type = prev_ret
            self._in_method = prev_method
            self._current_class = prev_class
            self.symbol_table.exit_scope()

        elif node_type == "class":
            class_name, _parent, members = node[1], node[2], node[3]
            self.symbol_table.enter_class(class_name)
            prev_class = self._current_class
            self._current_class = class_name
            # Spec §4.5: instance vars visible via this from definition to end of class
            visible_fields: set = set()
            for member in members:
                if member[0] == "var_def":
                    for fname in member[2]:
                        visible_fields.add(fname)
                elif member[0] == "method":
                    prev_visible = self._method_visible_fields
                    self._method_visible_fields = set(visible_fields)
                    self._check_ast_node(member)
                    self._method_visible_fields = prev_visible
            self._current_class = prev_class
            self.symbol_table.exit_class()

        elif node_type == "method":
            return_type, _name, params, body = node[1], node[2], node[3], node[4]
            self.symbol_table.enter_scope()
            prev_ret, prev_method, prev_class = (
                self._current_return_type,
                self._in_method,
                self._current_class,
            )
            self._current_return_type = return_type
            self._in_method = True
            if self._current_class:
                self.symbol_table.declare_symbol("this", self._current_class)
            for ptype, pname in self._normalize_params(params):
                if pname == "this":
                    self._semantic_error("Parameter cannot be named 'this'")
                    continue
                if not self._is_valid_data_type(ptype):
                    self._semantic_error(
                        f"Unknown parameter type '{ptype}' for '{pname}'"
                    )
                elif not self.symbol_table.declare_symbol(pname, ptype):
                    self._semantic_error(f"Parameter '{pname}' already declared")
            self._check_ast_node(body)
            self._current_return_type = prev_ret
            self._in_method = prev_method
            self._current_class = prev_class
            self.symbol_table.exit_scope()

        elif node_type == "var_def":
            # Only local var defs reach here (class fields handled separately)
            var_type, var_list = node[1], node[2]
            for var_name in var_list:
                self._declare_local(var_name, var_type)

        elif node_type == "assign":
            var_name, expr = node[1], node[2]
            symbol = self.symbol_table.lookup_symbol(var_name)
            if not symbol:
                self._semantic_error(f"Undeclared variable '{var_name}'")
                self._expr_type(expr)
            else:
                et = self._expr_type(expr)
                if et is not None and not self._types_compatible(symbol.type, et):
                    self._semantic_error(
                        f"Cannot assign '{et}' to variable '{var_name}' "
                        f"of type '{symbol.type}'",
                        EXIT_SEMANTIC_TYPE,
                    )

        elif node_type == "field_assign":
            obj_expr, field_name, value_expr = node[1], node[2], node[3]
            if self._reject_this_super_cascade(obj_expr):
                self._expr_type(value_expr)
            else:
                obj_t = self._expr_type(obj_expr)
                vt = self._expr_type(value_expr)
                if not obj_t or not self.symbol_table.is_class_type(obj_t):
                    self._semantic_error(
                        f"Field assignment on non-object type '{obj_t}'",
                        EXIT_SEMANTIC_TYPE,
                    )
                else:
                    field = self._lookup_field_access(obj_expr, obj_t, field_name)
                    if not field:
                        self._semantic_error(
                            f"Unknown field '{field_name}' on type '{obj_t}'"
                        )
                    elif vt is not None and not self._types_compatible(field.type, vt):
                        self._semantic_error(
                            f"Cannot assign '{vt}' to field '{field_name}' "
                            f"of type '{field.type}'",
                            EXIT_SEMANTIC_TYPE,
                        )

        elif node_type in (
            "binary",
            "unary",
            "int_lit",
            "str_lit",
            "var",
            "primary",
            "new",
            "cast",
            "this",
            "super",
            "field_access",
            "function_call",
            "function_call_expr",
            "method_call",
            "method_call_expr",
        ):
            # Expression statements / nested exprs: full type check
            if node_type in ("function_call", "method_call"):
                # statement form
                self._expr_type(node)
            elif node_type in ("function_call_expr", "method_call_expr"):
                self._expr_type(node)
            else:
                self._expr_type(node)

        elif node_type == "if" or node_type == "if_else":
            self._check_condition(node[1], "if")
            self._check_scoped_statements(node[2])
            if node_type == "if_else":
                self._check_scoped_statements(node[3])

        elif node_type == "while":
            self._check_condition(node[1], "while")
            self._check_scoped_statements(node[2])

        elif node_type == "return":
            expr = node[1]
            expected = self._current_return_type
            if expected is None:
                self._semantic_error("Return outside of function or method")
            elif expected == "void":
                if expr is not None:
                    self._semantic_error(
                        "void function/method cannot return a value",
                        EXIT_SEMANTIC_TYPE,
                    )
                    self._expr_type(expr)
            else:
                if expr is None:
                    self._semantic_error(
                        f"Non-void function/method must return a value "
                        f"of type '{expected}'",
                        EXIT_SEMANTIC_TYPE,
                    )
                else:
                    at = self._expr_type(expr)
                    # Skip follow-on type errors when the expression already failed.
                    if at is not None and not self._types_compatible(expected, at):
                        self._semantic_error(
                            f"Return type '{at}' incompatible with '{expected}'",
                            EXIT_SEMANTIC_TYPE,
                        )

        elif node_type == "block":
            self.symbol_table.enter_scope()
            for statement in node[1]:
                self._check_ast_node(statement)
            self.symbol_table.exit_scope()

        else:
            for child in node[1:]:
                if isinstance(child, (list, tuple)):
                    self._check_ast_node(child)

    def get_errors(self):
        return [message for _code, message in self.errors]

    def get_warnings(self):
        return self.warnings


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(
            "Usage: python compiler.py <input_file> [output_file]",
            file=sys.stderr,
        )
        sys.exit(EXIT_INTERNAL)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else "out.vc"

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(EXIT_INTERNAL)

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except OSError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(EXIT_INTERNAL)

    compiler = Compiler()
    sys.exit(compiler.compile(source_code, output_file))


if __name__ == "__main__":
    main()
