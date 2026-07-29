import unittest
from app.engines.parser_engine.javascript_parser import JavaScriptParser


class TestJavaScriptParser(unittest.TestCase):

    def setUp(self):
        self.parser = JavaScriptParser()

    def test_language_name(self):
        self.assertEqual(self.parser.language_name, "JavaScript")

    def test_extract_function_declaration(self):
        code = "function greet(name) {\n  return name;\n}"
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        fn = result.functions[0]
        self.assertEqual(fn.name, "greet")
        self.assertIn("name", fn.parameters)

    def test_extract_arrow_function(self):
        code = "const add = (a, b) => a + b;"
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        self.assertEqual(result.functions[0].name, "add")

    def test_extract_class(self):
        code = "class Animal {\n  constructor() {}\n}"
        result = self.parser.parse(code)
        self.assertEqual(len(result.classes), 1)
        self.assertEqual(result.classes[0].name, "Animal")

    def test_extract_class_with_extends(self):
        code = "class Dog extends Animal {\n  bark() {}\n}"
        result = self.parser.parse(code)
        self.assertEqual(len(result.classes), 1)
        cls = result.classes[0]
        self.assertEqual(cls.name, "Dog")
        self.assertIsNotNone(cls.bases)
        self.assertIn("Animal", cls.bases)

    def test_extract_method(self):
        code = "class Foo {\n  bar() {}\n  static baz() {}\n}"
        result = self.parser.parse(code)
        self.assertEqual(len(result.methods), 2)
        names = {m.name for m in result.methods}
        self.assertIn("bar", names)
        self.assertIn("baz", names)

    def test_extract_constructor(self):
        code = "class Foo {\n  constructor(x) {\n    this.x = x;\n  }\n}"
        result = self.parser.parse(code)
        constructors = [m for m in result.methods if m.is_constructor]
        self.assertEqual(len(constructors), 1)

    def test_extract_static_method(self):
        code = "class Foo {\n  static create() {\n    return new Foo();\n  }\n}"
        result = self.parser.parse(code)
        static_methods = [m for m in result.methods if m.is_static]
        self.assertEqual(len(static_methods), 1)
        self.assertEqual(static_methods[0].name, "create")

    def test_extract_import(self):
        code = 'import { useState } from "react";'
        result = self.parser.parse(code)
        self.assertGreaterEqual(len(result.imports), 1)
        imp = next((i for i in result.imports if i.name == "useState"), None)
        self.assertIsNotNone(imp)
        self.assertEqual(imp.module, "react")

    def test_extract_default_import(self):
        code = 'import React from "react";'
        result = self.parser.parse(code)
        default_imports = [i for i in result.imports if i.is_default]
        self.assertGreaterEqual(len(default_imports), 1)

    def test_extract_namespace_import(self):
        code = 'import * as path from "path";'
        result = self.parser.parse(code)
        wildcard = [i for i in result.imports if i.is_wildcard]
        self.assertGreaterEqual(len(wildcard), 1)

    def test_extract_export(self):
        code = "export function greet() {}\nexport default class Foo {}"
        result = self.parser.parse(code)
        self.assertGreaterEqual(len(result.exports), 1)
        defaults = [e for e in result.exports if e.is_default]
        self.assertGreaterEqual(len(defaults), 1)

    def test_extract_const_variable(self):
        code = 'const API_URL = "http://localhost";'
        result = self.parser.parse(code)
        self.assertEqual(len(result.variables), 1)
        self.assertEqual(result.variables[0].name, "API_URL")
        self.assertTrue(result.variables[0].is_constant)

    def test_extract_let_variable(self):
        code = "let count = 0;"
        result = self.parser.parse(code)
        self.assertEqual(len(result.variables), 1)
        self.assertFalse(result.variables[0].is_constant)

    def test_extract_comments(self):
        code = "// single line\n/* block */\n/** jsdoc */\nconst x = 1;"
        result = self.parser.parse(code)
        self.assertGreaterEqual(len(result.comments), 3)
        jsdoc = [c for c in result.comments if c.is_docstring]
        self.assertGreaterEqual(len(jsdoc), 1)

    def test_empty_source(self):
        result = self.parser.parse("")
        self.assertEqual(result.total_nodes, 0)
        self.assertIsNone(result.error)

    def test_syntax_error_still_parses(self):
        code = "function foo( {"
        result = self.parser.parse(code)
        self.assertIsNotNone(result.error)

    def test_parse_result_total_nodes(self):
        code = 'import x from "y";\nconst a = 1;\nfunction foo() {}\nclass Bar { baz() {} }'
        result = self.parser.parse(code)
        self.assertGreater(result.total_nodes, 0)


if __name__ == "__main__":
    unittest.main()
