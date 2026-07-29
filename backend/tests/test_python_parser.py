import unittest
from app.engines.parser_engine.python_parser import PythonParser


class TestPythonParser(unittest.TestCase):

    def setUp(self):
        self.parser = PythonParser()

    def test_language_name(self):
        self.assertEqual(self.parser.language_name, "Python")

    def test_extract_function(self):
        code = 'def greet(name: str) -> str:\n    """Say hello."""\n    return f"Hello {name}"'
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        fn = result.functions[0]
        self.assertEqual(fn.name, "greet")
        self.assertIn("name", fn.parameters)
        self.assertEqual(fn.return_type, "str")
        self.assertEqual(fn.start_line, 1)
        self.assertIsNotNone(fn.docstring)
        self.assertIn("Say hello", fn.docstring)

    def test_extract_async_function(self):
        code = "async def fetch(url):\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        self.assertEqual(result.functions[0].name, "fetch")

    def test_extract_class(self):
        code = "class Animal:\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.classes), 1)
        self.assertEqual(result.classes[0].name, "Animal")

    def test_extract_class_with_bases(self):
        code = "class Dog(Animal):\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.classes), 1)
        cls = result.classes[0]
        self.assertEqual(cls.name, "Dog")
        self.assertIn("Animal", cls.bases)

    def test_extract_abstract_class(self):
        code = "from abc import ABC\nclass Base(ABC):\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.classes), 1)
        self.assertTrue(result.classes[0].is_abstract)

    def test_extract_class_docstring(self):
        code = 'class Foo:\n    """Foo class."""\n    pass'
        result = self.parser.parse(code)
        self.assertEqual(len(result.classes), 1)
        self.assertIn("Foo class", result.classes[0].docstring)

    def test_extract_method(self):
        code = "class Foo:\n    def bar(self):\n        pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.methods), 1)
        self.assertEqual(result.methods[0].name, "bar")
        self.assertEqual(result.methods[0].class_name, "Foo")

    def test_extract_constructor(self):
        code = "class Foo:\n    def __init__(self, x):\n        self.x = x"
        result = self.parser.parse(code)
        self.assertEqual(len(result.methods), 1)
        self.assertTrue(result.methods[0].is_constructor)

    def test_extract_static_method(self):
        code = "class Foo:\n    @staticmethod\n    def bar():\n        pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.methods), 1)
        self.assertTrue(result.methods[0].is_static)

    def test_method_not_counted_as_function(self):
        code = "class Foo:\n    def bar(self):\n        pass\ndef baz():\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        self.assertEqual(result.functions[0].name, "baz")
        self.assertEqual(len(result.methods), 1)
        self.assertEqual(result.methods[0].name, "bar")

    def test_extract_import(self):
        code = "import os"
        result = self.parser.parse(code)
        self.assertEqual(len(result.imports), 1)
        self.assertEqual(result.imports[0].name, "os")

    def test_extract_from_import(self):
        code = "from os.path import join"
        result = self.parser.parse(code)
        self.assertEqual(len(result.imports), 1)
        imp = result.imports[0]
        self.assertEqual(imp.name, "join")
        self.assertIn("os", imp.module)

    def test_extract_wildcard_import(self):
        code = "from os.path import *"
        result = self.parser.parse(code)
        self.assertEqual(len(result.imports), 1)
        self.assertTrue(result.imports[0].is_wildcard)

    def test_extract_aliased_import(self):
        code = "import numpy as np"
        result = self.parser.parse(code)
        self.assertEqual(len(result.imports), 1)
        self.assertEqual(result.imports[0].alias, "np")

    def test_extract_variable(self):
        code = "x = 42"
        result = self.parser.parse(code)
        self.assertEqual(len(result.variables), 1)
        self.assertEqual(result.variables[0].name, "x")
        self.assertFalse(result.variables[0].is_constant)

    def test_extract_constant(self):
        code = "MAX_SIZE = 100"
        result = self.parser.parse(code)
        self.assertEqual(len(result.variables), 1)
        self.assertEqual(result.variables[0].name, "MAX_SIZE")
        self.assertTrue(result.variables[0].is_constant)

    def test_extract_comment(self):
        code = "# This is a comment\nx = 1"
        result = self.parser.parse(code)
        comments = [c for c in result.comments if not c.is_docstring]
        self.assertGreaterEqual(len(comments), 1)
        self.assertIn("comment", comments[0].text)

    def test_extract_decorated_function(self):
        code = "@decorator\ndef foo():\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(len(result.functions), 1)
        self.assertIsNotNone(result.functions[0].decorators)
        self.assertIn("decorator", result.functions[0].decorators)

    def test_parse_result_total_nodes(self):
        code = "import os\nx = 1\ndef foo():\n    pass\nclass Bar:\n    def baz(self):\n        pass"
        result = self.parser.parse(code)
        self.assertGreater(result.total_nodes, 0)

    def test_syntax_error_still_parses(self):
        code = "def foo(\n"
        result = self.parser.parse(code)
        self.assertIsNotNone(result.error)

    def test_empty_source(self):
        result = self.parser.parse("")
        self.assertEqual(result.total_nodes, 0)
        self.assertIsNone(result.error)

    def test_line_numbers(self):
        code = "x = 1\n\ndef foo():\n    pass"
        result = self.parser.parse(code)
        self.assertEqual(result.variables[0].start_line, 1)
        self.assertEqual(result.functions[0].start_line, 3)


if __name__ == "__main__":
    unittest.main()
