"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

from typing import Dict, List, Optional, OrderedDict as ODType
from collections import OrderedDict


HEADER_SIZE = 3  # [0]=VMT, [1]=parent VMT, [2]=class name


class MethodInfo:
    def __init__(self, name: str, return_type: str, params: list, body, owner: str):
        self.name = name
        self.return_type = return_type
        self.params = params  # list of (type, name) - without this
        self.body = body
        self.owner = owner  # defining class

    @property
    def label(self) -> str:
        return f"{self.owner}:{self.name}"

    @property
    def is_constructor(self) -> bool:
        return self.name == self.owner


class ClassInfo:
    def __init__(self, name: str, parent_name: str):
        self.name = name
        self.parent_name = parent_name
        self.parent: Optional["ClassInfo"] = None
        self.fields: OrderedDict[str, str] = OrderedDict()  # name -> type
        self.methods: OrderedDict[str, MethodInfo] = OrderedDict()

    def add_field(self, name: str, typ: str):
        self.fields[name] = typ

    def add_method(self, method: MethodInfo):
        self.methods[method.name] = method

    def all_fields(self) -> OrderedDict:
        if self.parent is None:
            return OrderedDict(self.fields)
        combined = OrderedDict(self.parent.all_fields())
        combined.update(self.fields)
        return combined

    def field_offset(self, name: str) -> int:
        fields = list(self.all_fields().keys())
        return HEADER_SIZE + fields.index(name)

    def object_size(self) -> int:
        return HEADER_SIZE + len(self.all_fields())

    def vmt(self) -> OrderedDict:
        """Method simple name -> MethodInfo (child overrides parent)."""
        if self.parent is None:
            return OrderedDict(self.methods)
        result = OrderedDict(self.parent.vmt())
        for name, method in self.methods.items():
            result[name] = method
        return result

    def vmt_index(self, method_name: str) -> int:
        return list(self.vmt().keys()).index(method_name)

    def constructor_chain(self) -> List[MethodInfo]:
        """Constructors from outermost ancestor to this class."""
        chain = []
        cur = self
        while cur is not None:
            ctor = cur.methods.get(cur.name)
            if ctor is not None:
                chain.append(ctor)
            cur = cur.parent
        chain.reverse()
        return chain


def build_class_model(ast) -> Dict[str, ClassInfo]:
    """Build class model from a program AST. Includes built-in Object."""
    classes: Dict[str, ClassInfo] = {}

    # Built-in Object
    obj = ClassInfo("Object", None)
    obj.parent_name = None
    obj.methods["toString"] = MethodInfo("toString", "string", [], None, "Object")
    obj.methods["getClass"] = MethodInfo("getClass", "string", [], None, "Object")
    classes["Object"] = obj

    if not ast or ast[0] != "program":
        return classes

    # Pass 1: create ClassInfo shells
    for defn in ast[1]:
        if defn[0] != "class":
            continue
        name, parent, members = defn[1], defn[2], defn[3]
        classes[name] = ClassInfo(name, parent)

    # Pass 2: link parents + members
    for defn in ast[1]:
        if defn[0] != "class":
            continue
        name, parent, members = defn[1], defn[2], defn[3]
        info = classes[name]
        info.parent = classes.get(parent)
        for member in members:
            if member[0] == "var_def":
                ftype, names = member[1], member[2]
                for fname in names:
                    info.add_field(fname, ftype)
            elif member[0] == "method":
                ret, mname, params, body = member[1], member[2], member[3], member[4]
                param_pairs = [(p[1], p[2]) for p in params]
                info.add_method(MethodInfo(mname, ret, param_pairs, body, name))

    return classes


def class_declaration_order(classes: Dict[str, ClassInfo]) -> List[str]:
    """Parents before children; Object first."""
    ordered = []
    visited = set()

    def visit(name):
        if name in visited or name not in classes:
            return
        info = classes[name]
        if info.parent_name:
            visit(info.parent_name)
        elif info.parent:
            visit(info.parent.name)
        visited.add(name)
        ordered.append(name)

    visit("Object")
    for name in classes:
        visit(name)
    return ordered
