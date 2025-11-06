"""Optimized AST data collector for single tree traversal."""

import ast
from typing import Optional


class ASTCollector:
    """Class for collecting all necessary data from AST in a single pass."""

    def __init__(self, tree: ast.AST):
        """Initialize collector.

        Args:
            tree: AST tree for analysis
        """
        self.tree = tree

        # Data is collected when collect() is called
        self.imports: list[ast.Import] = []
        self.import_froms: list[ast.ImportFrom] = []
        self.dag_calls: list[ast.Call] = []
        self.operators: list[ast.Call] = []
        self.assignments: list[ast.Assign] = []
        self.default_args: Optional[ast.Assign] = None
        self.task_assignments: dict[str, ast.Assign] = {}
        self.with_statements: list[ast.With] = []
        self.rshift_lshift_ops: list[tuple[ast.RShift | ast.LShift, int, int]] = []
        self.upstream_downstream_calls: list[ast.Call] = []
        self.top_level_calls: list[ast.Call] = []
        self.kubernetes_operators: list[ast.Call] = []

        # Dictionaries for fast lookup
        self.nodes_by_type: dict[type, list[ast.AST]] = {}

    def collect(self):
        """Collect all data in a single AST traversal.

        Traverses the AST tree once and collects all necessary data:
        imports, DAG calls, operators, assignments, etc.
        Should be called after initialization before using collected data.
        """
        self._walk(self.tree)

    def _walk(self, node: ast.AST):
        """Recursive AST traversal with data collection.

        Args:
            node: AST node to traverse
        """
        node_type = type(node)

        # Save all nodes by type for fast access
        if node_type not in self.nodes_by_type:
            self.nodes_by_type[node_type] = []
        self.nodes_by_type[node_type].append(node)

        # Collect specific node types
        if isinstance(node, ast.Import):
            self.imports.append(node)
        elif isinstance(node, ast.ImportFrom):
            self.import_froms.append(node)
        elif isinstance(node, ast.Assign):
            self.assignments.append(node)
            # Check default_args
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "default_args":
                    self.default_args = node
            # Save all assignments for task search
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.task_assignments[target.id] = node
        elif isinstance(node, ast.Call):
            # Check various call types
            func = node.func
            func_name = None

            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr

            if func_name:
                # DAG calls
                if func_name == "DAG" or (isinstance(func, ast.Name) and func.id == "DAG"):
                    self.dag_calls.append(node)
                # Operators
                elif "Operator" in func_name:
                    self.operators.append(node)
                    # Kubernetes operators
                    if "KubernetesPodOperator" in func_name:
                        self.kubernetes_operators.append(node)
                # upstream/downstream methods
                elif func_name in ["set_upstream", "set_downstream", "upstream", "downstream"]:
                    self.upstream_downstream_calls.append(node)
                # Top-level calls (for checking BP001, BP002, AIRFLINT003)
                # This is simplified check - detailed check will be in rules
                self.top_level_calls.append(node)

        elif isinstance(node, ast.With):
            self.with_statements.append(node)
        elif isinstance(node, (ast.RShift, ast.LShift)):
            # RShift and LShift don't have lineno directly, get from parent or use 0
            lineno = getattr(node, "lineno", 0) or 0
            col_offset = getattr(node, "col_offset", 0) or 0
            self.rshift_lshift_ops.append((node, lineno, col_offset))

        # Recursively process child nodes
        for child in ast.iter_child_nodes(node):
            self._walk(child)

    def has_dag_import(self) -> bool:
        """Check if DAG is imported from airflow.

        Returns:
            True if DAG is imported (via import or from import)
        """
        # Check regular imports
        for imp in self.imports:
            for alias in imp.names:
                if "airflow" in alias.name and "DAG" in alias.name:
                    return True

        # Check from imports
        for imp_from in self.import_froms:
            if imp_from.module and "airflow" in imp_from.module:
                for alias in imp_from.names:
                    if alias.name == "DAG":
                        return True

        return False

    def get_default_args_dict(self) -> Optional[dict]:
        """Get default_args dictionary from AST.

        Extracts key-value pairs from default_args dictionary assignment.
        Only extracts simple constant values (strings, numbers, etc.).

        Returns:
            Dictionary with default_args values, or None if not found or invalid
        """
        if not self.default_args or not isinstance(self.default_args.value, ast.Dict):
            return None

        result = {}
        dict_node = self.default_args.value
        keys = dict_node.keys
        values = dict_node.values

        for key, value in zip(keys, values):
            if isinstance(key, ast.Constant):
                key_value = key.value
                if isinstance(value, ast.Constant):
                    result[key_value] = value.value

        return result

    def has_default_args_key(self, key: str) -> bool:
        """Check if key exists in default_args dictionary.

        Args:
            key: Key name to check (e.g., "owner", "retries")

        Returns:
            True if key exists in default_args
        """
        default_args_dict = self.get_default_args_dict()
        if (
            default_args_dict
            and self.default_args
            and isinstance(self.default_args.value, ast.Dict)
        ):
            # Check via AST more accurately
            dict_node = self.default_args.value
            for k in dict_node.keys:
                if isinstance(k, ast.Constant) and k.value == key:
                    return True
        return False
