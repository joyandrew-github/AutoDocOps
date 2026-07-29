import unittest
from app.engines.parser_engine.typescript_parser import TypeScriptParser


class TestTypeScriptParser(unittest.TestCase):

    def setUp(self):
        self.parser = TypeScriptParser()

    def test_language_name(self):
        self.assertEqual(self.parser.language_name, "TypeScript")

    def test_extract_function_with_return_type(self):
        code = "function greet(name: string): string {\n  return name;\n}"
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        fn = result.functions[0]
        self.assertEqual(fn.name, "greet")
        self.assertIsNotNone(fn.return_type)
        self.assertIn("string", fn.return_type)

    def test_extract_interface(self):
        code = "interface User {\n  name: string;\n  age: number;\n}"
        result = self.parser.parse(code)
        interfaces = [c for c in result.classes if c.interfaces == "interface"]
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0].name, "User")
        self.assertTrue(interfaces[0].is_abstract)

    def test_extract_class_with_implements(self):
        code = "class Dog extends Animal {\n  bark(): void {}\n}"
        result = self.parser.parse(code)
        classes = [c for c in result.classes if c.interfaces != "interface"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, "Dog")

    def test_extract_abstract_class(self):
        code = "abstract class Shape {\n  abstract area(): number;\n}"
        result = self.parser.parse(code)
        self.assertTrue(result.classes[0].is_abstract)

    def test_extract_typed_variable(self):
        code = "const count: number = 5;"
        result = self.parser.parse(code)
        self.assertEqual(len(result.variables), 1)
        v = result.variables[0]
        self.assertEqual(v.name, "count")
        self.assertTrue(v.is_constant)

    def test_extract_enum(self):
        code = "enum Color {\n  Red,\n  Green,\n  Blue\n}"
        result = self.parser.parse(code)
        enums = [v for v in result.variables if v.var_type == "enum"]
        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0].name, "Color")

    def test_extract_type_alias(self):
        code = "type ID = string | number;"
        result = self.parser.parse(code)
        aliases = [v for v in result.variables if v.var_type == "type_alias"]
        self.assertEqual(len(aliases), 1)
        self.assertEqual(aliases[0].name, "ID")

    def test_extract_import(self):
        code = 'import { Component } from "react";'
        result = self.parser.parse(code)
        self.assertGreaterEqual(len(result.imports), 1)

    def test_extract_export(self):
        code = "export function add(a: number, b: number): number { return a + b; }"
        result = self.parser.parse(code)
        self.assertGreaterEqual(len(result.exports), 1)

    def test_extract_method_return_type(self):
        code = "class Calc {\n  add(a: number, b: number): number {\n    return a + b;\n  }\n}"
        result = self.parser.parse(code)
        self.assertEqual(len(result.methods), 1)

    def test_extract_comments(self):
        code = "// line comment\n/** JSDoc comment */\nconst x = 1;"
        result = self.parser.parse(code)
        self.assertGreaterEqual(len(result.comments), 2)

    def test_empty_source(self):
        result = self.parser.parse("")
        self.assertEqual(result.total_nodes, 0)

    def test_parse_result_total_nodes(self):
        code = 'import { x } from "y";\nconst a: number = 1;\nfunction foo(): void {}\ninterface Bar {}'
        result = self.parser.parse(code)
        self.assertGreater(result.total_nodes, 0)


if __name__ == "__main__":
    unittest.main()
