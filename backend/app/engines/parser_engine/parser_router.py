from app.engines.parser_engine.base_parser import BaseParser
from app.engines.parser_engine.python_parser import PythonParser
from app.engines.parser_engine.javascript_parser import JavaScriptParser
from app.engines.parser_engine.typescript_parser import TypeScriptParser
from app.core.logging import get_logger

logger = get_logger(__name__)


class ParserRouter:
    """Routes files to the appropriate language parser based on detected language.

    To add a new language:
    1. Create a parser class extending BaseParser
    2. Register it in PARSER_REGISTRY below
    """

    PARSER_REGISTRY: dict[str, type[BaseParser]] = {
        "Python": PythonParser,
        "JavaScript": JavaScriptParser,
        "TypeScript": TypeScriptParser,
    }

    def __init__(self):
        self._parser_cache: dict[str, BaseParser] = {}

    @classmethod
    def supported_languages(cls) -> list[str]:
        """Return list of languages that can be parsed."""
        return list(cls.PARSER_REGISTRY.keys())

    def get_parser(self, language: str) -> BaseParser | None:
        """Get the appropriate parser for a language. Returns None if unsupported."""
        if language not in self.PARSER_REGISTRY:
            return None

        if language not in self._parser_cache:
            parser_cls = self.PARSER_REGISTRY[language]
            self._parser_cache[language] = parser_cls()
            logger.debug(f"Instantiated parser for {language}")

        return self._parser_cache[language]

    def is_supported(self, language: str) -> bool:
        """Check if a language is supported for parsing."""
        return language in self.PARSER_REGISTRY

    @classmethod
    def register_parser(cls, language: str, parser_class: type[BaseParser]) -> None:
        """Register a new parser for a language at runtime."""
        cls.PARSER_REGISTRY[language] = parser_class
        logger.info(f"Registered parser for {language}: {parser_class.__name__}")
