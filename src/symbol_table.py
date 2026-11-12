"""
VYPa 2025 - VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""

from typing import Dict, Any, Optional, List

class Symbol:
    """Represents a symbol in the symbol table"""
    def __init__(self, name: str, symbol_type: str, value: Any = None, 
                 is_const: bool = False, scope_level: int = 0, 
                 is_method: bool = False, is_field: bool = False):
        self.name = name
        self.type = symbol_type
        self.value = value
        self.is_const = is_const
        self.scope_level = scope_level
        self.is_method = is_method
        self.is_field = is_field
        self.parameters = []  # For methods/functions
        self.return_type = None  # For methods/functions
    
    def __repr__(self):
        return f"Symbol({self.name}, {self.type}, {self.value}, const={self.is_const}, scope={self.scope_level}, method={self.is_method})"

class ClassInfo:
    """Represents a class definition"""
    def __init__(self, name: str, parent: Optional[str] = "Object"):
        self.name = name
        self.parent = parent  # None for Object root
        self.fields = {}  # field_name -> Symbol
        self.methods = {}  # method_name -> Symbol
        self.constructors = []  # List of constructors
    
    def add_field(self, field: Symbol):
        """Add a field to the class"""
        self.fields[field.name] = field
    
    def add_method(self, method: Symbol):
        """Add a method to the class"""
        self.methods[method.name] = method
    
    def add_constructor(self, constructor: Symbol):
        """Add a constructor to the class"""
        self.constructors.append(constructor)
    
    def get_field(self, name: str) -> Optional[Symbol]:
        """Get field by name"""
        return self.fields.get(name)
    
    def get_method(self, name: str) -> Optional[Symbol]:
        """Get method by name"""
        return self.methods.get(name)
    
    def __repr__(self):
        return f"ClassInfo({self.name}, parent={self.parent}, fields={len(self.fields)}, methods={len(self.methods)})"

class SymbolTable:
    """Symbol table with scope management for VYPlanguage"""
    
    def __init__(self):
        self.scopes = [{}]  # List of dictionaries for each scope level
        self.current_scope = 0
        self.classes = {}  # class_name -> ClassInfo
        self.functions = {}  # function_name -> Symbol
        self.current_class = None  # Current class being processed
        
        # Add built-in Object class
        self._add_builtin_object_class()
    
    def _add_builtin_object_class(self):
        """Add the built-in Object class"""
        object_class = ClassInfo("Object", parent=None)

        toString_method = Symbol("toString", "string", is_method=True)
        toString_method.return_type = "string"
        toString_method.parameters = []
        object_class.add_method(toString_method)

        getClass_method = Symbol("getClass", "string", is_method=True)
        getClass_method.return_type = "string"
        getClass_method.parameters = []
        object_class.add_method(getClass_method)

        self.classes["Object"] = object_class
    
    def enter_scope(self):
        """Enter a new scope"""
        self.current_scope += 1
        self.scopes.append({})
    
    def exit_scope(self):
        """Exit current scope"""
        if self.current_scope > 0:
            self.scopes.pop()
            self.current_scope -= 1
    
    def declare_symbol(self, name: str, symbol_type: str, value: Any = None, 
                      is_const: bool = False, is_method: bool = False, 
                      is_field: bool = False) -> bool:
        """Declare a new symbol in current scope"""
        if name in self.scopes[self.current_scope]:
            return False  # Symbol already declared in this scope
        
        symbol = Symbol(name, symbol_type, value, is_const, self.current_scope, 
                       is_method, is_field)
        self.scopes[self.current_scope][name] = symbol
        return True
    
    def lookup_symbol(self, name: str) -> Optional[Symbol]:
        """Look up symbol starting from current scope"""
        for scope_level in range(self.current_scope, -1, -1):
            if name in self.scopes[scope_level]:
                return self.scopes[scope_level][name]
        return None
    
    def update_symbol(self, name: str, value: Any) -> bool:
        """Update symbol value"""
        symbol = self.lookup_symbol(name)
        if symbol and not symbol.is_const:
            symbol.value = value
            return True
        return False
    
    def declare_class(self, name: str, parent: str = "Object") -> bool:
        """Declare a new class"""
        if name in self.classes:
            return False  # Class already declared
        
        class_info = ClassInfo(name, parent)
        self.classes[name] = class_info
        return True
    
    def get_class(self, name: str) -> Optional[ClassInfo]:
        """Get class information by name"""
        return self.classes.get(name)
    
    def enter_class(self, class_name: str):
        """Enter a class definition scope"""
        self.current_class = class_name
    
    def exit_class(self):
        """Exit class definition scope"""
        self.current_class = None
    
    def add_class_field(self, field_name: str, field_type: str) -> bool:
        """Add a field to the current class"""
        if not self.current_class:
            return False
        
        class_info = self.get_class(self.current_class)
        if not class_info:
            return False
        
        field = Symbol(field_name, field_type, is_field=True)
        class_info.add_field(field)
        return True
    
    def add_class_method(self, method_name: str, return_type: str, 
                         parameters: List[tuple] = None) -> bool:
        """Add a method to the current class"""
        if not self.current_class:
            return False
        
        class_info = self.get_class(self.current_class)
        if not class_info:
            return False
        
        method = Symbol(method_name, return_type, is_method=True)
        method.return_type = return_type
        method.parameters = parameters or []
        class_info.add_method(method)
        return True
    
    def add_class_constructor(self, constructor_name: str, 
                             parameters: List[tuple] = None) -> bool:
        """Add a constructor to the current class"""
        if not self.current_class:
            return False
        
        class_info = self.get_class(self.current_class)
        if not class_info:
            return False
        
        constructor = Symbol(constructor_name, "void", is_method=True)
        constructor.return_type = "void"
        constructor.parameters = parameters or []
        class_info.add_constructor(constructor)
        return True
    
    def declare_function(self, name: str, return_type: str, 
                        parameters: List[tuple] = None) -> bool:
        """Declare a global function"""
        if name in self.functions:
            return False  # Function already declared
        
        function = Symbol(name, return_type, is_method=True)
        function.return_type = return_type
        function.parameters = parameters or []
        self.functions[name] = function
        return True
    
    def get_function(self, name: str) -> Optional[Symbol]:
        """Get function by name"""
        return self.functions.get(name)
    
    def is_subclass(self, subclass: str, superclass: str) -> bool:
        """True if subclass is the same as or inherits from superclass."""
        if subclass == superclass:
            return True
        class_info = self.get_class(subclass)
        if not class_info:
            return False
        seen = set()
        current = class_info.parent
        while current and current not in seen:
            if current == superclass:
                return True
            seen.add(current)
            parent_class = self.get_class(current)
            if not parent_class:
                break
            current = parent_class.parent
        return False

    def lookup_field(self, class_name: str, field_name: str) -> Optional[Symbol]:
        """Look up an instance field along the inheritance chain."""
        seen = set()
        current = class_name
        while current and current not in seen:
            seen.add(current)
            info = self.get_class(current)
            if not info:
                return None
            field = info.get_field(field_name)
            if field:
                return field
            current = info.parent
        return None

    def lookup_method(self, class_name: str, method_name: str) -> Optional[Symbol]:
        """Look up a method along the inheritance chain (child overrides)."""
        seen = set()
        current = class_name
        while current and current not in seen:
            seen.add(current)
            info = self.get_class(current)
            if not info:
                return None
            method = info.get_method(method_name)
            if method:
                return method
            current = info.parent
        return None

    def is_class_type(self, type_name: str) -> bool:
        return type_name in self.classes
    
    def get_all_symbols(self) -> Dict[str, Symbol]:
        """Get all symbols from all scopes"""
        all_symbols = {}
        for scope in self.scopes:
            all_symbols.update(scope)
        return all_symbols
    
    def __repr__(self):
        result = "Symbol Table:\n"
        result += f"Classes: {list(self.classes.keys())}\n"
        result += f"Functions: {list(self.functions.keys())}\n"
        for i, scope in enumerate(self.scopes):
            result += f"  Scope {i}:\n"
            for name, symbol in scope.items():
                result += f"    {symbol}\n"
        return result

# Global symbol table instance
symbol_table = SymbolTable()

if __name__ == "__main__":
    # Test the symbol table
    st = SymbolTable()
    
    # Declare a class
    st.declare_class("Shape", "Object")
    st.enter_class("Shape")
    st.add_class_field("id", "int")
    st.add_class_method("toString", "string")
    st.add_class_constructor("Shape")
    st.exit_class()
    
    # Declare some symbols
    st.declare_symbol("x", "int", 10)
    st.declare_symbol("y", "string", "hello")
    
    # Look up symbols
    print("Lookup x:", st.lookup_symbol("x"))
    print("Lookup y:", st.lookup_symbol("y"))
    print("Shape class:", st.get_class("Shape"))
    print("Object class:", st.get_class("Object"))
    
    print(st)