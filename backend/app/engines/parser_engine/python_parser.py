import tree_sitter_python
from tree_sitter import Language, Node
from app.engines.parser_engine.base_parser import (
    BaseParser,
    ParsedFunction,
    ParsedClass,
    ParsedMethod,
    ParsedImport,
    ParsedVariable,
    ParsedComment,
)


class PythonParser(BaseParser):
    """Tree-sitter based parser for Python source code."""

    @property
    def language_name(self) -> str:
        return "Python"

    def get_language(self) -> Language:
        return Language(tree_sitter_python.language())

    def _get_decorators(self, node: Node, source: str) -> str | None:
        """Extract decorator list from a function/class definition."""
        decorators = []
        prev = node.prev_named_sibling
        while prev and prev.type == "decorator":
            decorators.insert(0, self._node_text(prev, source).strip())
            prev = prev.prev_named_sibling
        return ", ".join(decorators) if decorators else None

    def _get_docstring(self, node: Node, source: str) -> str | None:
        """Extract docstring from a function/class body."""
        body = node.child_by_field_name("body")
        if body and body.named_children:
            first = body.named_children[0]
            if first.type == "expression_statement":
                expr = first.named_children[0] if first.named_children else None
                if expr and expr.type == "string":
                    text = self._node_text(expr, source)
                    return text.strip("\"'").strip()
        return None

    def extract_functions(self, root: Node, source: str) -> list[ParsedFunction]:
        results: list[ParsedFunction] = []
        for node in self._find_descendants_by_type(root, "function_definition"):
            # Skip methods (those inside class bodies)
            if node.parent and node.parent.type == "block":
                grandparent = node.parent.parent
                if grandparent and grandparent.type == "class_definition":
                    continue

            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            params_node = node.child_by_field_name("parameters")
            ret_node = node.child_by_field_name("return_type")
            body_node = node.child_by_field_name("body")

            is_async = node.parent and node.parent.type == "decorated_definition"
            # Check for async keyword
            actual_node = node
            if node.prev_named_sibling and node.prev_named_sibling.type == "decorator":
                pass
            for child in (node.parent.children if node.parent else []):
                if child.type == "async" or (hasattr(child, 'text') and child.text == b"async"):
                    is_async = True
                    break

            # Check for yield in body
            is_generator = bool(self._find_descendants_by_type(node, "yield"))

            results.append(ParsedFunction(
                name=self._node_text(name_node, source),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                parameters=self._node_text(params_node, source) if params_node else None,
                return_type=self._node_text(ret_node, source) if ret_node else None,
                decorators=self._get_decorators(node, source),
                is_async=is_async,
                is_generator=is_generator,
                docstring=self._get_docstring(node, source),
                body_start_line=body_node.start_point[0] + 1 if body_node else None,
                body_end_line=body_node.end_point[0] + 1 if body_node else None,
            ))
        return results

    def extract_classes(self, root: Node, source: str) -> list[ParsedClass]:
        results: list[ParsedClass] = []
        for node in self._find_descendants_by_type(root, "class_definition"):
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue

            # Extract base classes
            bases = None
            superclasses = node.child_by_field_name("superclasses")
            if superclasses:
                bases = self._node_text(superclasses, source)

            # Check if abstract (has ABC or ABCMeta in bases, or has abstractmethod)
            is_abstract = False
            if bases and ("ABC" in bases or "ABCMeta" in bases):
                is_abstract = True

            results.append(ParsedClass(
                name=self._node_text(name_node, source),
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                bases=bases,
                decorators=self._get_decorators(node, source),
                docstring=self._get_docstring(node, source),
                is_abstract=is_abstract,
            ))
        return results

    def extract_methods(self, root: Node, source: str) -> list[ParsedMethod]:
        results: list[ParsedMethod] = []
        for class_node in self._find_descendants_by_type(root, "class_definition"):
            class_name_node = class_node.child_by_field_name("name")
            if not class_name_node:
                continue
            class_name = self._node_text(class_name_node, source)

            body = class_node.child_by_field_name("body")
            if not body:
                continue

            for method_node in self._find_descendants_by_type(body, "function_definition"):
                name_node = method_node.child_by_field_name("name")
                if not name_node:
                    continue

                method_name = self._node_text(name_node, source)
                params_node = method_node.child_by_field_name("parameters")
                ret_node = method_node.child_by_field_name("return_type")

                decorators = self._get_decorators(method_node, source)
                is_static = bool(decorators and "staticmethod" in decorators)
                is_constructor = method_name == "__init__"

                results.append(ParsedMethod(
                    name=method_name,
                    class_name=class_name,
                    start_line=method_node.start_point[0] + 1,
                    end_line=method_node.end_point[0] + 1,
                    start_column=method_node.start_point[1],
                    end_column=method_node.end_point[1],
                    parameters=self._node_text(params_node, source) if params_node else None,
                    return_type=self._node_text(ret_node, source) if ret_node else None,
                    decorators=decorators,
                    is_static=is_static,
                    is_constructor=is_constructor,
                    docstring=self._get_docstring(method_node, source),
                ))
        return results

    def extract_imports(self, root: Node, source: str) -> list[ParsedImport]:
        results: list[ParsedImport] = []

        # import x
        for node in self._find_descendants_by_type(root, "import_statement"):
            for name_node in self._find_children_by_type(node, "dotted_name", "aliased_import"):
                if name_node.type == "aliased_import":
                    actual = name_node.child_by_field_name("name")
                    alias_node = name_node.child_by_field_name("alias")
                    results.append(ParsedImport(
                        name=self._node_text(actual, source) if actual else None,
                        module=self._node_text(actual, source) if actual else None,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                        alias=self._node_text(alias_node, source) if alias_node else None,
                    ))
                else:
                    results.append(ParsedImport(
                        name=self._node_text(name_node, source),
                        module=self._node_text(name_node, source),
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                    ))

        # from x import y
        for node in self._find_descendants_by_type(root, "import_from_statement"):
            module_node = node.child_by_field_name("module_name")
            module_name = self._node_text(module_node, source) if module_node else None

            # Check for wildcard
            if any(c.type == "wildcard_import" for c in node.children):
                results.append(ParsedImport(
                    name="*",
                    module=module_name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    is_wildcard=True,
                ))
                continue

            for name_node in self._find_children_by_type(node, "dotted_name", "aliased_import"):
                # Skip the module name node (has field 'module_name')
                if node.field_name_for_child(node.children.index(name_node)) == "module_name":
                    continue
                if name_node.type == "aliased_import":
                    actual = name_node.child_by_field_name("name")
                    alias_node = name_node.child_by_field_name("alias")
                    results.append(ParsedImport(
                        name=self._node_text(actual, source) if actual else None,
                        module=module_name,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                        alias=self._node_text(alias_node, source) if alias_node else None,
                    ))
                else:
                    results.append(ParsedImport(
                        name=self._node_text(name_node, source),
                        module=module_name,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        start_column=node.start_point[1],
                        end_column=node.end_point[1],
                    ))

        return results

    def extract_variables(self, root: Node, source: str) -> list[ParsedVariable]:
        results: list[ParsedVariable] = []

        # Module-level assignments
        for node in root.children:
            if node.type == "expression_statement":
                for assign in self._find_children_by_type(node, "assignment"):
                    left = assign.child_by_field_name("left")
                    right = assign.child_by_field_name("right")
                    type_node = assign.child_by_field_name("type")
                    if left and left.type == "identifier":
                        name = self._node_text(left, source)
                        results.append(ParsedVariable(
                            name=name,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            start_column=node.start_point[1],
                            end_column=node.end_point[1],
                            var_type=self._node_text(type_node, source) if type_node else None,
                            is_constant=name.isupper(),
                            scope="module",
                            initial_value=self._node_text(right, source)[:200] if right else None,
                        ))

        return results

    def extract_comments(self, root: Node, source: str) -> list[ParsedComment]:
        results: list[ParsedComment] = []

        for node in self._find_descendants_by_type(root, "comment"):
            text = self._node_text(node, source)
            results.append(ParsedComment(
                text=text,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_column=node.start_point[1],
                end_column=node.end_point[1],
                comment_type="line",
                is_docstring=False,
            ))

        # Extract docstrings as comments too
        for node in self._find_descendants_by_type(root, "expression_statement"):
            if node.named_children and node.named_children[0].type == "string":
                parent = node.parent
                if parent and parent.type == "block":
                    gp = parent.parent
                    if gp and gp.type in ("function_definition", "class_definition", "module"):
                        # Check if this is the first statement
                        idx = list(parent.named_children).index(node) if node in parent.named_children else -1
                        if idx == 0:
                            text = self._node_text(node.named_children[0], source)
                            results.append(ParsedComment(
                                text=text.strip("\"'").strip(),
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                start_column=node.start_point[1],
                                end_column=node.end_point[1],
                                comment_type="docstring",
                                is_docstring=True,
                            ))

        return results
