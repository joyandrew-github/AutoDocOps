import unittest
from app.engines.parser_engine.parser_router import ParserRouter
from app.engines.parser_engine.base_parser import BaseParser
from app.engines.parser_engine.python_parser import PythonParser
from app.engines.parser_engine.javascript_parser import JavaScriptParser
from app.engines.parser_engine.typescript_parser import TypeScriptParser


class TestParserRouter(unittest.TestCase):

    def setUp(self):
        self.router = ParserRouter()

    def test_supported_languages(self):
        langs = ParserRouter.supported_languages()
        self.assertIn("Python", langs)
        self.assertIn("JavaScript", langs)
        self.assertIn("TypeScript", langs)

    def test_get_python_parser(self):
        parser = self.router.get_parser("Python")
        self.assertIsNotNone(parser)
        self.assertIsInstance(parser, PythonParser)
        self.assertEqual(parser.language_name, "Python")

    def test_get_javascript_parser(self):
        parser = self.router.get_parser("JavaScript")
        self.assertIsNotNone(parser)
        self.assertIsInstance(parser, JavaScriptParser)
        self.assertEqual(parser.language_name, "JavaScript")

    def test_get_typescript_parser(self):
        parser = self.router.get_parser("TypeScript")
        self.assertIsNotNone(parser)
        self.assertIsInstance(parser, TypeScriptParser)
        self.assertEqual(parser.language_name, "TypeScript")

    def test_unsupported_language_returns_none(self):
        parser = self.router.get_parser("Haskell")
        self.assertIsNone(parser)

    def test_is_supported(self):
        self.assertTrue(self.router.is_supported("Python"))
        self.assertTrue(self.router.is_supported("JavaScript"))
        self.assertTrue(self.router.is_supported("TypeScript"))
        self.assertFalse(self.router.is_supported("Ruby"))

    def test_parser_caching(self):
        parser1 = self.router.get_parser("Python")
        parser2 = self.router.get_parser("Python")
        self.assertIs(parser1, parser2)

    def test_register_parser(self):
        class DummyParser(BaseParser):
            @property
            def language_name(self):
                return "Dummy"
            def get_language(self):
                pass
            def extract_functions(self, root, source):
                return []
            def extract_classes(self, root, source):
                return []
            def extract_methods(self, root, source):
                return []
            def extract_imports(self, root, source):
                return []
            def extract_variables(self, root, source):
                return []
            def extract_comments(self, root, source):
                return []

        ParserRouter.register_parser("Dummy", DummyParser)
        self.assertTrue(self.router.is_supported("Dummy"))
        parser = self.router.get_parser("Dummy")
        self.assertIsInstance(parser, DummyParser)
        # Clean up
        del ParserRouter.PARSER_REGISTRY["Dummy"]


if __name__ == "__main__":
    unittest.main()
