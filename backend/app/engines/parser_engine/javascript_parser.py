import tree_sitter_javascript
from tree_sitter import Language, Node
from app.engines.parser_engine.base_parser import (
    BaseParser,
    ParsedFunction,
    ParsedClass,
    ParsedMethod,
    ParsedImport,
    ParsedExport,
    ParsedVariable,
    ParsedComment,
)


class JavaScriptParser(BaseParser):
    """Tree-sitter based parser for JavaScript source code."""

    @property
    def language_name(self) -> str:
        return "JavaScript"

    def get_language(self) -> Language:
        return Language(tree_sitter_javascript.language())

    def _get_params(self, node: Node, source: str) -> str | None:
        params = node.child_by_field_name("parameters")
        return self._node_text(params, source) if params else None

    def extract_functions(self, root: Node, source: str) -> list[ParsedFunction]:
        results: list[ParsedFunction] = []

        # function declarations
        for node in self._find_descendants_by_type(root, "function_declaration"):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            # Skip if inside a class body
            parent = node.parent
            while parent:
                if parent.type == "class_body":
                    break
                parent = parent.parent
            if parent and parent.type == "class_body":
                continue

            is_async = any(c.type == "async" for c in node.children) if node.children else False
            is_generator = node.type == "generator_function_declaration" or any(
                c.type == "*" for c in node.children
            )
            body = node.child_by_field_name("body")

            results.append(ParsedFunction(
                name=self._node_text(name_node, source),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                parameters=self._get_params(node, source),
                is_async=is_async,
                is_generator=is_generator,
                body_start_line=body.start_point[0] + 1 if body else None,
                body_end_line=body.end_point[0] + 1 if body else None,
            ))

        # Arrow functions and function expressions assigned to variables
        for node in self._find_descendants_by_type(root, "lexical_declaration", "variable_declaration"):
            for declarator in self._find_children_by_type(node, "variable_declarator"):
                name_node = declarator.child_by_field_name("name")
                value_node = declarator.child_by_field_name("value")
                if not name_node or not value_node:
                    continue
                if value_node.type in ("arrow_function", "function_expression", "function"):
                    is_async = any(c.type == "async" for c in value_node.children)
                    body = value_node.child_by_field_name("body")
                    results.append(ParsedFunction(
                        name=self._node_text(name_node, source),
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                        parameters=self._get_params(value_node, source),
                        is_async=is_async,
                        body_start_line=body.start_point[0] + 1 if body else None,
                        body_end_line=body.end_point[0] + 1 if body else None,
                    ))

        return results

    def extract_classes(self, root: Node, source: str) -> list[ParsedClass]:
        results: list[ParsedClass] = []
        for node in self._find_descendants_by_type(root, "class_declaration", "class"):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            # Heritage (extends)
            bases = None
            heritage = node.child_by_field_name("heritage") or next(
                (c for c in node.children if c.type == "class_heritage"), None
            )
            if heritage:
                bases = self._node_text(heritage, source)

            results.append(ParsedClass(
                name=self._node_text(name_node, source),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                bases=bases,
            ))
        return results

    def extract_methods(self, root: Node, source: str) -> list[ParsedMethod]:
        results: list[ParsedMethod] = []
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
                is_static = any(c.type == "static" for c in method_node.children)
                is_async = any(c.type == "async" for c in method_node.children)
                is_constructor = method_name == "constructor"

                results.append(ParsedMethod(
                    name=method_name,
                    class_name=class_name,
                    start_line=method_node.start_point[0] + 1,
                    end_line=method_node.end_point[0] + 1,
                    start_column=method_node.start_point[1],
                    end_column=method_node.end_point[1],
                    parameters=self._get_params(method_node, source),
                    is_static=is_static,
                    is_async=is_async,
                    is_constructor=is_constructor,
                ))
        return results

    def extract_imports(self, root: Node, source: str) -> list[ParsedImport]:
        results: list[ParsedImport] = []

        for node in self._find_descendants_by_type(root, "import_statement"):
            source_node = node.child_by_field_name("source")
            module = self._node_text(source_node, source).strip("'\"") if source_node else None

            # import specifiers
            for spec in self._find_descendants_by_type(node, "import_specifier"):
                name_node = spec.child_by_field_name("name")
                alias_node = spec.child_by_field_name("alias")
                results.append(ParsedImport(
                    name=self._node_text(name_node, source) if name_node else None,
                    module=module,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    alias=self._node_text(alias_node, source) if alias_node else None,
                ))

            # Default import
            for clause in self._find_children_by_type(node, "import_clause"):
                for ident in self._find_children_by_type(clause, "identifier"):
                    results.append(ParsedImport(
                        name=self._node_text(ident, source),
                        module=module,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                        is_default=True,
                    ))

            # Namespace import (import * as X)
            for ns in self._find_descendants_by_type(node, "namespace_import"):
                alias_ident = next((c for c in ns.children if c.type == "identifier"), None)
                results.append(ParsedImport(
                    name="*",
                    module=module,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    alias=self._node_text(alias_ident, source) if alias_ident else None,
                    is_wildcard=True,
                ))

            # If no specifiers found, record the whole import
            if not results or results[-1].start_line != node.start_point[0] + 1:
                results.append(ParsedImport(
                    name=None,
                    module=module,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                ))

        # require() calls
        for node in self._find_descendants_by_type(root, "call_expression"):
            func = node.child_by_field_name("function")
            if func and self._node_text(func, source) == "require":
                args = node.child_by_field_name("arguments")
                if args and args.named_children:
                    module = self._node_text(args.named_children[0], source).strip("'\"")
                    # Find the variable name this is assigned to
                    name = None
                    parent = node.parent
                    if parent and parent.type == "variable_declarator":
                        name_node = parent.child_by_field_name("name")
                        name = self._node_text(name_node, source) if name_node else None
                    results.append(ParsedImport(
                        name=name,
                        module=module,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                    ))

        return results

    def extract_exports(self, root: Node, source: str) -> list[ParsedExport]:
        results: list[ParsedExport] = []
        for node in self._find_descendants_by_type(root, "export_statement"):
            is_default = any(c.type == "default" for c in node.children)

            # Named exports
            for spec in self._find_descendants_by_type(node, "export_specifier"):
                name_node = spec.child_by_field_name("name")
                results.append(ParsedExport(
                    name=self._node_text(name_node, source) if name_node else None,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    is_default=is_default,
                    exported_type="named",
                ))

            # Default or declaration exports
            declaration = node.child_by_field_name("declaration")
            if declaration:
                name_node = declaration.child_by_field_name("name")
                name = self._node_text(name_node, source) if name_node else None
                exported_type = declaration.type
                results.append(ParsedExport(
                    name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    is_default=is_default,
                    exported_type=exported_type,
                ))

            # If nothing specific found, record the export
            if not any(r.start_line == node.start_point[0] + 1 for r in results):
                value = node.child_by_field_name("value")
                results.append(ParsedExport(
                    name=self._node_text(value, source) if value else None,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    is_default=is_default,
                ))

        return results

    def extract_variables(self, root: Node, source: str) -> list[ParsedVariable]:
        results: list[ParsedVariable] = []
        for node in self._find_descendants_by_type(root, "lexical_declaration", "variable_declaration"):
            # Skip if parent is export
            kind = None
            for child in node.children:
                if child.type in ("const", "let", "var"):
                    kind = child.type
                    break

            for declarator in self._find_children_by_type(node, "variable_declarator"):
                name_node = declarator.child_by_field_name("name")
                value_node = declarator.child_by_field_name("value")
                if not name_node:
                    continue

                # Skip arrow functions / function expressions (handled in extract_functions)
                if value_node and value_node.type in ("arrow_function", "function_expression", "function"):
                    continue

                name = self._node_text(name_node, source)
                results.append(ParsedVariable(
                    name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    is_constant=kind == "const",
                    scope="module" if node.parent and node.parent.type == "program" else "local",
                    initial_value=self._node_text(value_node, source)[:200] if value_node else None,
                ))

        return results

    def extract_comments(self, root: Node, source: str) -> list[ParsedComment]:
        results: list[ParsedComment] = []
        for node in self._find_descendants_by_type(root, "comment"):
            text = self._node_text(node, source)
            comment_type = "block" if text.startswith("/*") else "line"
            is_docstring = text.startswith("/**")
            results.append(ParsedComment(
                text=text,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                comment_type=comment_type,
                is_docstring=is_docstring,
            ))
        return results
