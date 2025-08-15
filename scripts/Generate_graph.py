import os
from tree_sitter_language_pack import get_parser
import json
import sys
import traceback
import argparse


class GraphGenerator:
    def __init__(self, lang):
        self.graph = {"nodes": [], "edges": []}
        self._sources = {}  # file_path -> source bytes
        self._trees = {}  # file_path -> tree

        # Normalize language name for tree-sitter compatibility
        lang_normalized = self._normalize_language(lang.lower())
        self.parser = get_parser(lang_normalized)
        self.language = lang.lower()
        self._node_id_counter = 0
        self._visited_functions = set()
        self._function_definitions = {}  # function_name -> {file_path, definition}

    def _normalize_language(self, lang):
        """Normalize language names for tree-sitter parser compatibility."""
        lang_map = {
            'c++': 'cpp',
            'objective-c': 'objc',
            'c#': 'csharp',
        }
        return lang_map.get(lang, lang)

    def build_graph(self, repo_path, function_name, file_path=None):
        """
        Build a reverse call tree for the specified function.
        repo_path: root of the codebase
        function_name: name of the function to trace callers for
        file_path: optional, not used in reverse tree mode
        """
        # Reset state
        self.graph = {"nodes": [], "edges": []}
        self._sources = {}
        self._node_id_counter = 0
        self._visited_functions = set()
        self._function_definitions = {}

        # Parse all files in the repo
        self._parse_all_files(repo_path)

        # Debug: Print tree-sitter AST for the file containing the function
        target_def_for_debug = self._find_function_definition(function_name)
        if target_def_for_debug:
            file_path_for_debug = target_def_for_debug['file']
            if file_path_for_debug in self._trees:
                tree_for_debug = self._trees[file_path_for_debug]
                # print(f"--- Tree-sitter AST for {file_path_for_debug} ---", file=sys.stderr)
                # The string representation of a node is its S-expression.
                # print(str(tree_for_debug.root_node), file=sys.stderr)
                # print("--- End Tree-sitter AST ---", file=sys.stderr)

        # Create root node for target function
        target_def = self._find_function_definition(function_name)
        root_id = self._add_node(function_name, [], None, target_def)

        # Build reverse call tree
        self._build_reverse_tree(function_name, root_id)

        return self.graph

    def _parse_all_files(self, repo_path):
        """Parse all relevant files in the repository."""
        extensions = {
            'python': ['.py'],
            'go': ['.go'],
            'c': ['.c', '.h'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.h'],
            'c++': ['.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.h'],
            'objc': ['.m', '.mm', '.h'],
            'objective-c': ['.m', '.mm', '.h'],
            'rust': ['.rs'],
            'verilog': ['.v', '.sv'],
            'move': ['.mv'],
            'cairo': ['.cairo'],
            'c#': ['.cs'],
            'solidity': ['.sol'],
            'java': ['.java'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx']
        }

        valid_extensions = extensions.get(self.language, [])

        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                file_extension = os.path.splitext(file)[1]
                if file_extension in valid_extensions:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            source = f.read()
                        source_bytes = source.encode('utf-8')
                        self._sources[file_path] = source_bytes
                        tree = self.parser.parse(source_bytes)
                        self._trees[file_path] = tree

                        # Extract function definitions
                        self._extract_function_definitions(file_path, source_bytes, tree)
                    except Exception:
                        # Skip files that can't be read
                        pass

    def _extract_function_definitions(self, file_path, source, tree):
        """Extract all function definitions from a file."""
        root = tree.root_node

        # Find all function definitions
        self._find_all_function_definitions(root, source, file_path)

    def _find_all_function_definitions(self, node, source, file_path):
        """Recursively find all function definitions in the file."""
        # Handle function definitions by language type
        if self._handle_function_definition(node, source, file_path):
            pass  # Function was handled by specific language processor

        # Recurse into children
        for child in node.children:
            self._find_all_function_definitions(child, source, file_path)

    def _handle_function_definition(self, node, source, file_path):
        """Handle function definition for specific language and node type."""
        handlers = {
            'rust': self._handle_rust_function,
            'python': self._handle_python_function,
            'go': self._handle_go_function,
            'c': self._handle_c_function,
            'cpp': self._handle_cpp_function,
            'c++': self._handle_cpp_function,
            'objc': self._handle_objc_function,
            'objective-c': self._handle_objc_function,
            'c#': self._handle_csharp_function,
            'solidity': self._handle_solidity_function,
            'java': self._handle_java_function,
            'javascript': self._handle_javascript_function,
        }

        handler = handlers.get(self.language)
        if handler:
            return handler(node, source, file_path)
        return False

    def _handle_rust_function(self, node, source, file_path):
        if node.type == 'function_item':
            return self._extract_simple_function(node, source, file_path)
        return False

    def _handle_python_function(self, node, source, file_path):
        if node.type == 'function_definition':
            return self._extract_simple_function(node, source, file_path)
        return False

    def _handle_go_function(self, node, source, file_path):
        if node.type == 'function_declaration':
            return self._extract_simple_function(node, source, file_path)
        return False

    def _handle_c_function(self, node, source, file_path):
        if node.type == 'function_definition':
            return self._extract_declarator_function(node, source, file_path)
        return False

    def _handle_cpp_function(self, node, source, file_path):
        if node.type == 'function_definition':
            return self._extract_declarator_function(node, source, file_path)
        elif node.type == 'template_declaration':
            return self._extract_template_function(node, source, file_path)
        return False

    def _handle_objc_function(self, node, source, file_path):
        if node.type in ['method_declaration', 'method_definition']:
            method_selector = self._extract_objc_method_selector(node, source)
            if method_selector:
                function_def = self._get_node_text(node, source)

                parameters = []
                for child in node.children:
                    if child.type == 'parameter_declaration':
                        parameters.append(self._get_node_text(child, source))
                parameters_text = ", ".join(parameters) if parameters else None

                return_type = None
                return_type_node = self._find_node_of_type(node, 'method_type')
                if return_type_node:
                    return_type = self._get_node_text(return_type_node, source)

                self._store_function_definition(method_selector, file_path, function_def, parameters_text, return_type, node=node)
                return True
        elif node.type == 'function_definition':
            # Objective-C is a superset of C, so we also handle C-style functions
            return self._extract_declarator_function(node, source, file_path)
        return False

    def _handle_csharp_function(self, node, source, file_path):
        if node.type in ['method_declaration', 'constructor_declaration']:
            return self._extract_simple_function(node, source, file_path)
        return False

    def _handle_solidity_function(self, node, source, file_path):
        if node.type == 'function_definition':
            return self._extract_simple_function(node, source, file_path)
        return False

    def _handle_java_function(self, node, source, file_path):
        if node.type in ['method_declaration', 'constructor_declaration']:
            return self._extract_simple_function(node, source, file_path)
        return False

    def _handle_javascript_function(self, node, source, file_path):
        if node.type == 'function_declaration':
            return self._extract_simple_function(node, source, file_path)
        elif node.type == 'method_definition':
            return self._extract_simple_function(node, source, file_path)
        elif node.type in ['function', 'arrow_function']:
            parent = node.parent
            if parent and parent.type == 'variable_declarator':
                name_node = parent.child_by_field_name('name')
                if name_node:
                    function_name = self._get_node_text(name_node, source)
                    function_def = self._get_node_text(parent, source)
                    parameters, return_type = self._extract_function_signature(node, source)
                    self._store_function_definition(function_name, file_path, function_def, parameters, return_type, node=parent)
                    return True
        return False

    def _extract_simple_function(self, node, source, file_path):
        """Extract function with simple name field."""
        name_node = node.child_by_field_name('name')
        if name_node:
            function_name = self._get_node_text(name_node, source)
            function_def = self._get_node_text(node, source)
            parameters, return_type = self._extract_function_signature(node, source)
            self._store_function_definition(function_name, file_path, function_def, parameters, return_type, node=node)
            return True
        return False

    def _extract_declarator_function(self, node, source, file_path):
        """Extract function with declarator field (C/C++ style)."""
        declarator = node.child_by_field_name('declarator')
        if declarator:
            name_node = self._find_function_name_node(declarator)
            if name_node:
                function_name = self._get_node_text(name_node, source)
                function_def = self._get_node_text(node, source)

                return_type = self._get_node_text(node.child_by_field_name('type'), source) if node.child_by_field_name('type') else None

                parameters = None
                param_list_node = self._find_node_of_type(declarator, 'parameter_list')
                if param_list_node:
                    parameters = self._get_node_text(param_list_node, source)

                self._store_function_definition(function_name, file_path, function_def, parameters, return_type, node=node)
                return True
        return False

    def _extract_template_function(self, node, source, file_path):
        """Extract C++ template function."""
        for child in node.children:
            if child.type == 'function_definition':
                declarator = child.child_by_field_name('declarator')
                if declarator:
                    name_node = self._find_function_name_node(declarator)
                    if name_node:
                        function_name = self._get_node_text(name_node, source)
                        function_def = self._get_node_text(node, source)

                        return_type = self._get_node_text(child.child_by_field_name('type'), source) if child.child_by_field_name('type') else None

                        parameters = None
                        param_list_node = self._find_node_of_type(declarator, 'parameter_list')
                        if param_list_node:
                            parameters = self._get_node_text(param_list_node, source)

                        self._store_function_definition(function_name, file_path, function_def, parameters, return_type, node=node)
                        return True
        return False

    def _extract_function_signature(self, node, source):
        """Extract parameters and return type from a function node."""
        params_text, return_text = None, None

        lang_config = {
            'python': {'params': 'parameters', 'return': 'return_type'},
            'go': {'params': 'parameter_list', 'return': 'result'},
            'c#': {'params': 'parameter_list', 'return': 'return_type'},
            'solidity': {'params': 'parameters', 'return': 'returns'},
            'java': {'params': 'formal_parameters', 'return': 'type'},
            'javascript': {'params': 'parameters', 'return': 'return_type'},
            'rust': {'params': 'parameters', 'return': 'return_type'},
        }

        if self.language in lang_config:
            config = lang_config[self.language]
            params_node = node.child_by_field_name(config['params'])
            if params_node:
                params_text = self._get_node_text(params_node, source)

            return_node = node.child_by_field_name(config['return'])
            if return_node:
                return_text = self._get_node_text(return_node, source)

        return params_text, return_text

    def _store_function_definition(self, function_name, file_path, function_def, parameters=None, return_type=None, node=None):
        """Store a function definition."""
        if function_name not in self._function_definitions:
            self._function_definitions[function_name] = []

        self._function_definitions[function_name].append({
            'file': file_path,
            'code': function_def,
            'parameters': parameters,
            'return_type': return_type,
            'node': node
        })

    def _find_function_definition(self, function_name):
        """Find the definition of a function."""
        if function_name in self._function_definitions:
            defs = self._function_definitions[function_name]
            if not defs:
                return None

            # Heuristic: the longest definition is most likely the one with a body.
            # This handles cases where both a declaration (e.g., in a header file)
            # and a definition (with a body) are found for the same function.
            return max(defs, key=lambda d: len(d['code']))
        return None

    def _build_reverse_tree(self, target_function, target_node_id):
        """Recursively build the reverse call tree."""
        if target_function in self._visited_functions:
            return
        self._visited_functions.add(target_function)

        callers = self._find_callers(target_function)

        for caller_info in callers:
            caller_name = caller_info['function']
            arguments = caller_info['arguments']
            file_path = caller_info['file']

            # Get function definition
            function_def = self._find_function_definition(caller_name)

            # Add node for the caller
            caller_id = self._add_node(caller_name, arguments, file_path, function_def)

            # Add edge from caller to target
            self.graph["edges"].append({"from": caller_id, "to": target_node_id})

            # Recursively process the caller
            if caller_name != '<module>':  # Don't recurse on module-level calls
                self._build_reverse_tree(caller_name, caller_id)

    def _find_node_of_type(self, node, type_name):
        """Helper to find a descendant node of a specific type."""
        if not node:
            return None
        if node.type == type_name:
            return node
        queue = list(node.children)
        while queue:
            child = queue.pop(0)
            if child.type == type_name:
                return child
            queue.extend(child.children)
        return None

    def _find_callers(self, target_function):
        """Find all functions that call the target function."""
        callers = []

        for file_path, source in self._sources.items():
            tree = self._trees[file_path]
            root = tree.root_node

            # Find all calls to target function in this file
            calls = self._find_function_calls(root, target_function, source)

            for call_node, containing_function in calls:
                # Extract arguments from the call
                arguments = self._extract_arguments(call_node, source)

                callers.append({
                    'function': containing_function,
                    'arguments': arguments,
                    'file': file_path
                })

        return callers

    def _find_function_name_node(self, declarator_node):
        """Helper function to find the function name node in C-style languages."""
        if not declarator_node:
            return None
        if declarator_node.type == 'identifier':
            return declarator_node
        elif declarator_node.type == 'function_declarator':
            # For C function declarators, the name is in the declarator child
            return self._find_function_name_node(declarator_node.child_by_field_name('declarator'))
        elif declarator_node.type == 'pointer_declarator':
            return self._find_function_name_node(declarator_node.child_by_field_name('declarator'))
        elif declarator_node.type == 'parenthesized_declarator':
            # For parenthesized declarators, recurse into the declarator
            return self._find_function_name_node(declarator_node.child_by_field_name('declarator'))
        elif declarator_node.type == 'qualified_identifier':
            # For C++ qualified names like namespace::function
            name_node = declarator_node.child_by_field_name('name')
            if name_node:
                return name_node
        elif declarator_node.type == 'destructor_name':
            # For C++ destructors
            return declarator_node
        elif declarator_node.type == 'operator_name':
            # For C++ operator overloads
            return declarator_node
        elif declarator_node.type == 'template_function':
            # For C++ template functions
            name_node = declarator_node.child_by_field_name('name')
            if name_node:
                return name_node
        return None

    def _extract_objc_method_selector(self, method_node, source):
        """Extract method selector from Objective-C method declaration/definition."""
        selector_parts = []

        # Look for selector parts in method signature
        for child in method_node.children:
            if child.type == 'method_selector':
                # Extract all selector parts
                for selector_child in child.children:
                    if selector_child.type == 'selector':
                        selector_parts.append(self._get_node_text(selector_child, source))
            elif child.type == 'selector':
                selector_parts.append(self._get_node_text(child, source))
            elif child.type == 'keyword_argument':
                for arg_child in child.children:
                    if arg_child.type == 'selector':
                        selector_parts.append(self._get_node_text(arg_child, source))

        return ''.join(selector_parts) if selector_parts else None

    def _find_function_calls(self, node, target_name, source, current_function='<module>'):
        """Recursively find all calls to target_name, tracking the containing function."""
        calls = []

        # Update current function context
        current_function = self._update_current_function(node, source, current_function)

        # Check for function calls
        call_result = self._check_function_call(node, target_name, source, current_function)
        if call_result:
            calls.append(call_result)

        # Recurse into children
        for child in node.children:
            calls.extend(self._find_function_calls(child, target_name, source, current_function))

        return calls

    def _update_current_function(self, node, source, current_function):
        """Update the current function context based on node type and language."""
        update_handlers = {
            'python': lambda: self._get_simple_function_name(node, source) if node.type == 'function_definition' else None,
            'go': lambda: self._get_simple_function_name(node, source) if node.type == 'function_declaration' else None,
            'c': lambda: self._get_declarator_function_name(node, source) if node.type == 'function_definition' else None,
            'cpp': lambda: self._get_declarator_function_name(node, source) if node.type == 'function_definition' else None,
            'c++': lambda: self._get_declarator_function_name(node, source) if node.type == 'function_definition' else None,
            'objc': lambda: self._extract_objc_method_selector(node, source) if node.type in ['method_declaration', 'method_definition'] else None,
            'objective-c': lambda: self._extract_objc_method_selector(node, source) if node.type in ['method_declaration', 'method_definition'] else None,
            'c#': lambda: self._get_simple_function_name(node, source) if node.type in ['method_declaration', 'constructor_declaration'] else None,
            'solidity': lambda: self._get_simple_function_name(node, source) if node.type == 'function_definition' else None,
            'java': lambda: self._get_simple_function_name(node, source) if node.type in ['method_declaration', 'constructor_declaration'] else None,
            'javascript': lambda: self._get_javascript_function_name(node, source),
            'rust': lambda: self._get_simple_function_name(node, source) if node.type == 'function_item' else None,
        }

        handler = update_handlers.get(self.language)
        if handler:
            new_function = handler()
            if new_function:
                return new_function
        return current_function

    def _get_simple_function_name(self, node, source):
        """Get function name from simple name field."""
        name_node = node.child_by_field_name('name')
        return self._get_node_text(name_node, source) if name_node else None

    def _get_declarator_function_name(self, node, source):
        """Get function name from declarator field."""
        declarator = node.child_by_field_name('declarator')
        if declarator:
            name_node = self._find_function_name_node(declarator)
            return self._get_node_text(name_node, source) if name_node else None
        return None

    def _get_javascript_function_name(self, node, source):
        """Get JavaScript function name handling various patterns."""
        if node.type == 'function_declaration':
            return self._get_simple_function_name(node, source)
        elif node.type == 'method_definition':
            return self._get_simple_function_name(node, source)
        elif node.type in ['function', 'arrow_function']:
            parent = node.parent
            if parent and parent.type == 'variable_declarator':
                name_node = parent.child_by_field_name('name')
                return self._get_node_text(name_node, source) if name_node else None
        return None

    def _check_function_call(self, node, target_name, source, current_function):
        """Check if node represents a call to target_name."""
        call_handlers = {
            'python': self._check_python_call,
            'go': self._check_go_call,
            'c': self._check_c_call,
            'cpp': self._check_cpp_call,
            'c++': self._check_cpp_call,
            'objc': self._check_objc_call,
            'objective-c': self._check_objc_call,
            'c#': self._check_csharp_call,
            'solidity': self._check_solidity_call,
            'java': self._check_java_call,
            'javascript': self._check_javascript_call,
            'rust': self._check_rust_call,
        }

        handler = call_handlers.get(self.language)
        if handler:
            return handler(node, target_name, source, current_function)
        return None

    def _check_python_call(self, node, target_name, source, current_function):
        if node.type == 'call':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'attribute':
                    attr_node = func_node.child_by_field_name('attribute')
                    if attr_node:
                        call_name = self._get_node_text(attr_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _check_rust_call(self, node, target_name, source, current_function):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'field_expression':
                    field_node = func_node.child_by_field_name('field')
                    if field_node:
                        call_name = self._get_node_text(field_node, source)
                        if call_name == target_name:
                            return (node, current_function)
                elif func_node.type == 'scoped_identifier':
                    name_node = func_node.child_by_field_name('name')
                    if name_node:
                        call_name = self._get_node_text(name_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _check_go_call(self, node, target_name, source, current_function):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'selector_expression':
                    field_node = func_node.child_by_field_name('field')
                    if field_node:
                        call_name = self._get_node_text(field_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _check_c_call(self, node, target_name, source, current_function):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                call_name = None
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                elif func_node.type == 'field_expression':
                    field_node = func_node.child_by_field_name('field')
                    if field_node:
                        call_name = self._get_node_text(field_node, source)
                elif func_node.type == 'parenthesized_expression':
                    # Handle function pointer calls like (*func_ptr)()
                    if func_node.named_child_count == 1:
                        inner_expr = func_node.named_child(0)
                        if inner_expr.type == 'pointer_expression':
                            # In `(*func)`, `func` is the argument of the pointer_expression
                            arg_node = inner_expr.child_by_field_name('argument')
                            if arg_node and arg_node.type == 'identifier':
                                call_name = self._get_node_text(arg_node, source)

                if call_name and call_name == target_name:
                    return (node, current_function)
        return None

    def _check_cpp_call(self, node, target_name, source, current_function):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'field_expression':
                    field_node = func_node.child_by_field_name('field')
                    if field_node:
                        call_name = self._get_node_text(field_node, source)
                        if call_name == target_name:
                            return (node, current_function)
                elif func_node.type == 'qualified_identifier':
                    name_node = func_node.child_by_field_name('name')
                    if name_node:
                        call_name = self._get_node_text(name_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _check_objc_call(self, node, target_name, source, current_function):
        if node.type == 'message_expression':
            method_selector = self._extract_objc_method_selector(node, source)
            if method_selector and (method_selector == target_name or target_name in method_selector):
                return (node, current_function)

        # Objective-C is a superset of C, so also check for C-style function calls
        return self._check_c_call(node, target_name, source, current_function)

    def _check_csharp_call(self, node, target_name, source, current_function):
        if node.type == 'invocation_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'member_access_expression':
                    name_node = func_node.child_by_field_name('name')
                    if name_node:
                        call_name = self._get_node_text(name_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _check_solidity_call(self, node, target_name, source, current_function):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'member_expression':
                    property_node = func_node.child_by_field_name('property')
                    if property_node:
                        call_name = self._get_node_text(property_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _check_java_call(self, node, target_name, source, current_function):
        if node.type == 'method_invocation':
            name_node = node.child_by_field_name('name')
            if name_node:
                call_name = self._get_node_text(name_node, source)
                if call_name == target_name:
                    return (node, current_function)
        elif node.type == 'object_creation_expression':
            type_node = node.child_by_field_name('type')
            if not type_node:
                return None

            class_name = None

            # BFS to find the class identifier within simple, qualified, or generic types
            queue = [type_node]
            while queue:
                current_node = queue.pop(0)
                if current_node.type == 'type_identifier':
                    class_name = self._get_node_text(current_node, source)
                    break
                elif current_node.type == 'scoped_type_identifier':
                    name_node = current_node.child_by_field_name('name')
                    if name_node:
                        class_name = self._get_node_text(name_node, source)
                        break
                queue.extend(current_node.children)

            if class_name and class_name == target_name:
                return (node, current_function)

        return None

    def _check_javascript_call(self, node, target_name, source, current_function):
        if node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        return (node, current_function)
                elif func_node.type == 'member_expression':
                    property_node = func_node.child_by_field_name('property')
                    if property_node:
                        call_name = self._get_node_text(property_node, source)
                        if call_name == target_name:
                            return (node, current_function)
        return None

    def _extract_arguments(self, call_node, source):
        """Extract argument values from a function call."""
        arguments = []

        # Handle different argument node patterns by language
        args_node = call_node.child_by_field_name('arguments')

        # Some tree-sitter grammars might use different field names
        if not args_node:
            # Try alternative field names based on language
            if self.language == 'java':
                args_node = call_node.child_by_field_name('arguments')
            elif self.language == 'c#':
                args_node = call_node.child_by_field_name('argument_list')
            elif self.language in ['c', 'cpp', 'c++']:
                args_node = call_node.child_by_field_name('arguments')
            elif self.language in ['objc', 'objective-c']:
                # Objective-C message expressions have arguments as direct children
                for child in call_node.children:
                    if child.type == 'argument':
                        arg_text = self._get_node_text(child, source).strip()
                        if arg_text:
                            arguments.append(arg_text)
                return arguments

        if args_node:
            for child in args_node.children:
                if child.type not in ['(', ')', ',', '[', ']']:
                    arg_text = self._get_node_text(child, source).strip()
                    if arg_text:
                        arguments.append(arg_text)

        return arguments

    def _add_node(self, function_name, arguments, file_path, function_def=None):
        """Add a node to the graph and return its ID."""
        node_id = self._node_id_counter
        self._node_id_counter += 1

        node = {
            "id": node_id,
            "function": function_name,
            "arguments": arguments,
            "parameters": None,
            "return_type": None
        }

        if file_path:
            node["file"] = file_path

        if function_def:
            node["code"] = function_def.get('code')
            node["parameters"] = function_def.get('parameters')
            node["return_type"] = function_def.get('return_type')

        self.graph["nodes"].append(node)
        return node_id

    def _get_node_text(self, node, source):
        """Extract text from a node given the source bytes."""
        return source[node.start_byte:node.end_byte].decode('utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate reverse call tree for a function")
    parser.add_argument("repo_path", help="Path to codebase root")
    parser.add_argument("function_name", help="Function to trace callers for")
    parser.add_argument("file_path", nargs='?', help="Not used in reverse tree mode")
    parser.add_argument("--language", "-l", default="python",
                      help="Language to analyze (python, go, c, cpp, c++, objc, objective-c, rust, verilog, move, cairo, c#, solidity, java, javascript)")
    args = parser.parse_args()

    # Take the first function if multiple are provided, separated by newlines
    function_name = args.function_name.splitlines()[0]

    gen = GraphGenerator(args.language)
    try:
        graph = gen.build_graph(args.repo_path, function_name)
        print(json.dumps(graph, indent=4))
    except Exception as e:
        print(f"Error generating reverse call tree for function '{function_name}': {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
