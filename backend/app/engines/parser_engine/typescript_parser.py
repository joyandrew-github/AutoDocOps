import tree_sitter_typescript
from tree_sitter import Language, Node
from app.engines.parser_engine.javascript_parser import JavaScriptParser
from app.engines.parser_engine.base_parser import (
    ParsedFunction,
    ParsedClass,
    ParsedMethod,
    ParsedImport,
    ParsedExport,
    ParsedVariable,
    ParsedComment,
)


class TypeScriptParser(JavaScriptParser):
    """Tree-sitter based parser for TypeScript source code.

    Extends JavaScriptParser and adds TypeScript-specific features
    like interfaces, type annotations, and enums.
    """

    @property
    def language_name(self) -> str:
        return "TypeScript"

    def get_language(self) -> Language:
        return Language(tree_sitter_typescript.language_typescript())

    def _get_type_annotation(self, node: Node, source: str) -> str | None:
        """Extract type annotation from a node."""
        type_ann = node.child_by_field_name("return_type") or node.child_by_field_name("type")
        if type_ann:
            text = self._node_text(type_ann, source)
            return text.lstrip(":").strip()
        # Look for type_annotation child
        for child in node.children:
            if child.type == "type_annotation":
                return self._node_text(child, source).lstrip(":").strip()
        return None

    def extract_functions(self, root: Node, source: str) -> list[ParsedFunction]:
        results = super().extract_functions(root, source)

        # Add return types for functions that have them
        for node in self._find_descendants_by_type(root, "function_declaration"):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            name = self._node_text(name_node, source)
            ret_type = self._get_type_annotation(node, source)
            if ret_type:
                for fn in results:
                    if fn.name == name and fn.start_line == node.start_point[0] + 1:
                        fn.return_type = ret_type
                        break

        return results

    def extract_classes(self, root: Node, source: str) -> list[ParsedClass]:
        results = super().extract_classes(root, source)

        # Handle abstract_class_declaration (TypeScript specific)
        for node in self._find_descendants_by_type(root, "abstract_class_declaration"):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            # Heritage (extends)
            bases = None
            for child in node.children:
                if child.type == "class_heritage":
                    bases = self._node_text(child, source)
                    break

            results.append(ParsedClass(
                name=self._node_text(name_node, source),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                bases=bases,
                is_abstract=True,
            ))

        # Also extract interfaces as class-like constructs
        for node in self._find_descendants_by_type(root, "interface_declaration"):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            # Heritage (extends)
            bases = None
            for child in node.children:
                if child.type == "extends_type_clause":
                    bases = self._node_text(child, source)
                    break

            results.append(ParsedClass(
                name=self._node_text(name_node, source),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                bases=bases,
                is_abstract=True,
                interfaces="interface",
            ))

        return results

    def extract_methods(self, root: Node, source: str) -> list[ParsedMethod]:
        results = super().extract_methods(root, source)

        # Add return type annotations
        for class_node in self._find_descendants_by_type(root, "class_declaration", "class"):
            class_name_node = class_node.child_by_field_name("name")
            class_name = self._node_text(class_name_node, source) if class_name_node else "anonymous"

            body = class_node.child_by_field_name("body")
            if not body:
                continue

            for method_node in self._find_children_by_type(body, "method_definition"):
                name_node = method_node.child_by_field_name("name")
                if not name_node:
                    continue
                method_name = self._node_text(name_node, source)
                ret_type = self._get_type_annotation(method_node, source)
                if ret_type:
                    for m in results:
                        if m.name == method_name and m.class_name == class_name and m.start_line == method_node.start_point[0] + 1:
                            m.return_type = ret_type
                            break

        return results

    def extract_variables(self, root: Node, source: str) -> list[ParsedVariable]:
        results = super().extract_variables(root, source)

        # Add type annotations to variables
        for node in self._find_descendants_by_type(root, "lexical_declaration", "variable_declaration"):
            for declarator in self._find_children_by_type(node, "variable_declarator"):
                name_node = declarator.child_by_field_name("name")
                if not name_node:
                    continue
                var_type = self._get_type_annotation(declarator, source)
                if var_type:
                    name = self._node_text(name_node, source)
                    for v in results:
                        if v.name == name and v.start_line == node.start_point[0] + 1:
                            v.var_type = var_type
                            break

        # Extract enum declarations as variables
        for node in self._find_descendants_by_type(root, "enum_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                results.append(ParsedVariable(
                    name=self._node_text(name_node, source),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    var_type="enum",
                    is_constant=True,
                    scope="module",
                ))

        # Extract type aliases as variables
        for node in self._find_descendants_by_type(root, "type_alias_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                value_node = node.child_by_field_name("value")
                results.append(ParsedVariable(
                    name=self._node_text(name_node, source),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    var_type="type_alias",
                    is_constant=True,
                    scope="module",
                    initial_value=self._node_text(value_node, source)[:200] if value_node else None,
                ))

        return results
