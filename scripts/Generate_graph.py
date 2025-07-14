import os
from tree_sitter import Language, Parser
from tree_sitter_language_pack import get_binding, get_language, get_parser
from tomllib import load
import json
import sys
import traceback
import argparse


class GraphGenerator:
    def __init__(self, lang):
        self.graph = {"nodes": [], "edges": []}
        self._sources = {}  # file_path -> source bytes
        self.parser = get_parser(lang.lower())
        self.language = lang.lower()
        self._node_id_counter = 0
        self._visited_functions = set()
        self._function_definitions = {}  # function_name -> {file_path, definition}

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

                        # Extract function definitions
                        self._extract_function_definitions(file_path, source_bytes)
                    except Exception as e:
                        # Skip files that can't be read
                        pass

    def _extract_function_definitions(self, file_path, source):
        """Extract all function definitions from a file."""
        tree = self.parser.parse(source)
        root = tree.root_node

        # Find all function definitions
        self._find_all_function_definitions(root, source, file_path)

    def _find_all_function_definitions(self, node, source, file_path):
        """Recursively find all function definitions in the file."""
        # Python function definitions
        if self.language == 'python' and node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                function_name = self._get_node_text(name_node, source)
                function_def = self._get_node_text(node, source)
                self._store_function_definition(function_name, file_path, function_def)

        # Go function declarations
        elif self.language == 'go' and node.type == 'function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                function_name = self._get_node_text(name_node, source)
                function_def = self._get_node_text(node, source)
                self._store_function_definition(function_name, file_path, function_def)

        # C function declarations
        elif self.language == 'c' and node.type == 'function_definition':
            declarator = node.child_by_field_name('declarator')
            if declarator:
                name_node = self._find_function_name_node(declarator)
                if name_node:
                    function_name = self._get_node_text(name_node, source)
                    function_def = self._get_node_text(node, source)
                    self._store_function_definition(function_name, file_path, function_def)

        # C# method declarations
        elif self.language == 'c#' and node.type in ['method_declaration', 'constructor_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                function_name = self._get_node_text(name_node, source)
                function_def = self._get_node_text(node, source)
                self._store_function_definition(function_name, file_path, function_def)

        # Solidity function declarations
        elif self.language == 'solidity' and node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                function_name = self._get_node_text(name_node, source)
                function_def = self._get_node_text(node, source)
                self._store_function_definition(function_name, file_path, function_def)

        # Java method declarations
        elif self.language == 'java' and node.type in ['method_declaration', 'constructor_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                function_name = self._get_node_text(name_node, source)
                function_def = self._get_node_text(node, source)
                self._store_function_definition(function_name, file_path, function_def)

        # JavaScript function declarations and methods
        elif self.language == 'javascript' and node.type in ['function_declaration', 'method_definition', 'function', 'arrow_function']:
            # Handle different types of function definitions
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    function_name = self._get_node_text(name_node, source)
                    function_def = self._get_node_text(node, source)
                    self._store_function_definition(function_name, file_path, function_def)
            elif node.type == 'method_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    function_name = self._get_node_text(name_node, source)
                    function_def = self._get_node_text(node, source)
                    self._store_function_definition(function_name, file_path, function_def)
            elif node.type in ['function', 'arrow_function']:
                # For variable assignments like: const foo = function() {} or const bar = () => {}
                parent = node.parent
                if parent and parent.type == 'variable_declarator':
                    name_node = parent.child_by_field_name('name')
                    if name_node:
                        function_name = self._get_node_text(name_node, source)
                        function_def = self._get_node_text(parent, source)
                        self._store_function_definition(function_name, file_path, function_def)

        # Recurse into children
        for child in node.children:
            self._find_all_function_definitions(child, source, file_path)

    def _store_function_definition(self, function_name, file_path, function_def):
        """Store a function definition."""
        if function_name not in self._function_definitions:
            self._function_definitions[function_name] = []

        self._function_definitions[function_name].append({
            'file': file_path,
            'definition': function_def
        })

    def _find_function_definition(self, function_name):
        """Find the definition of a function."""
        if function_name in self._function_definitions:
            # Return the first definition found (could be enhanced to handle multiple definitions)
            return self._function_definitions[function_name][0]['definition']
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

    def _find_callers(self, target_function):
        """Find all functions that call the target function."""
        callers = []

        for file_path, source in self._sources.items():
            tree = self.parser.parse(source)
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
        if declarator_node.type == 'identifier':
            return declarator_node
        elif declarator_node.type == 'function_declarator':
            # For C function declarators, the name is in the declarator child
            return self._find_function_name_node(declarator_node.child_by_field_name('declarator'))
        elif declarator_node.type == 'parenthesized_declarator':
            # For parenthesized declarators, recurse into the declarator
            return self._find_function_name_node(declarator_node.child_by_field_name('declarator'))
        return None

    def _find_function_calls(self, node, target_name, source, current_function='<module>'):
        """Recursively find all calls to target_name, tracking the containing function."""
        calls = []

        # Update current function if we're in a function definition/declaration
        if self.language == 'python' and node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_function = self._get_node_text(name_node, source)
        elif self.language == 'go' and node.type == 'function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_function = self._get_node_text(name_node, source)
        elif self.language == 'c' and node.type == 'function_definition':
            declarator = node.child_by_field_name('declarator')
            if declarator:
                name_node = self._find_function_name_node(declarator)
                if name_node:
                    current_function = self._get_node_text(name_node, source)
        elif self.language == 'c#' and node.type in ['method_declaration', 'constructor_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                current_function = self._get_node_text(name_node, source)
        elif self.language == 'solidity' and node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_function = self._get_node_text(name_node, source)
        elif self.language == 'java' and node.type in ['method_declaration', 'constructor_declaration']:
            name_node = node.child_by_field_name('name')
            if name_node:
                current_function = self._get_node_text(name_node, source)
        elif self.language == 'javascript':
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    current_function = self._get_node_text(name_node, source)
            elif node.type == 'method_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    current_function = self._get_node_text(name_node, source)
            elif node.type in ['function', 'arrow_function']:
                parent = node.parent
                if parent and parent.type == 'variable_declarator':
                    name_node = parent.child_by_field_name('name')
                    if name_node:
                        current_function = self._get_node_text(name_node, source)

        # Check for calls to the target function
        if self.language == 'python' and node.type == 'call':
            func_node = node.child_by_field_name('function')
            if func_node:
                # Simple function calls
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        calls.append((node, current_function))
                # Attribute calls (e.g., obj.method)
                elif func_node.type == 'attribute':
                    attr_node = func_node.child_by_field_name('attribute')
                    if attr_node:
                        call_name = self._get_node_text(attr_node, source)
                        if call_name == target_name:
                            calls.append((node, current_function))

        elif self.language == 'go' and node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                # Simple function calls
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        calls.append((node, current_function))
                # Package calls (e.g., pkg.Function)
                elif func_node.type == 'selector_expression':
                    field_node = func_node.child_by_field_name('field')
                    if field_node:
                        call_name = self._get_node_text(field_node, source)
                        if call_name == target_name:
                            calls.append((node, current_function))

        elif self.language == 'c' and node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node and func_node.type == 'identifier':
                call_name = self._get_node_text(func_node, source)
                if call_name == target_name:
                    calls.append((node, current_function))

        elif self.language == 'c#' and node.type == 'invocation_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                # Simple method calls
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        calls.append((node, current_function))
                # Member access (e.g., obj.Method())
                elif func_node.type == 'member_access_expression':
                    name_node = func_node.child_by_field_name('name')
                    if name_node:
                        call_name = self._get_node_text(name_node, source)
                        if call_name == target_name:
                            calls.append((node, current_function))

        elif self.language == 'solidity' and node.type == 'call_expression':
            func_node = node.child_by_field_name('function')
            if func_node:
                # Simple function calls
                if func_node.type == 'identifier':
                    call_name = self._get_node_text(func_node, source)
                    if call_name == target_name:
                        calls.append((node, current_function))
                # Member access (e.g., contract.function())
                elif func_node.type == 'member_expression':
                    property_node = func_node.child_by_field_name('property')
                    if property_node:
                        call_name = self._get_node_text(property_node, source)
                        if call_name == target_name:
                            calls.append((node, current_function))

        elif self.language == 'java' and node.type == 'method_invocation':
            name_node = node.child_by_field_name('name')
            if name_node:
                call_name = self._get_node_text(name_node, source)
                if call_name == target_name:
                    calls.append((node, current_function))

        elif self.language == 'javascript':
            # Function calls
            if node.type == 'call_expression':
                func_node = node.child_by_field_name('function')
                if func_node:
                    # Simple function calls: foo()
                    if func_node.type == 'identifier':
                        call_name = self._get_node_text(func_node, source)
                        if call_name == target_name:
                            calls.append((node, current_function))
                    # Member expressions: obj.method()
                    elif func_node.type == 'member_expression':
                        property_node = func_node.child_by_field_name('property')
                        if property_node:
                            call_name = self._get_node_text(property_node, source)
                            if call_name == target_name:
                                calls.append((node, current_function))

        # Recurse into children
        for child in node.children:
            calls.extend(self._find_function_calls(child, target_name, source, current_function))

        return calls

    def _extract_arguments(self, call_node, source):
        """Extract argument values from a function call."""
        arguments = []

        # All languages use a similar pattern for argument extraction
        args_node = call_node.child_by_field_name('arguments')

        # Some tree-sitter grammars might use different field names
        if not args_node:
            # Try alternative field names based on language
            if self.language == 'java':
                args_node = call_node.child_by_field_name('arguments')
            elif self.language == 'c#':
                args_node = call_node.child_by_field_name('argument_list')

        if args_node:
            for child in args_node.children:
                if child.type not in ['(', ')', ',']:
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
            "arguments": arguments
        }

        if file_path:
            node["file"] = file_path

        if function_def:
            node["definition"] = function_def

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
    parser.add_argument("--language", "-l", default="python", help="Language to analyze (python, go, c, c#, solidity, java, javascript)")
    args = parser.parse_args()

    gen = GraphGenerator(args.language)
    try:
        graph = gen.build_graph(args.repo_path, args.function_name)
        print(json.dumps(graph, indent=4))
    except Exception as e:
        print(f"Error generating reverse call tree for function '{args.function_name}': {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
