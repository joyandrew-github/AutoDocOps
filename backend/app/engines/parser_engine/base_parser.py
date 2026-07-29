from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from tree_sitter import Language, Parser, Node


@dataclass
class ParsedFunction:
    name: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    parameters: str | None = None
    return_type: str | None = None
    decorators: str | None = None
    is_async: bool = False
    is_generator: bool = False
    docstring: str | None = None
    body_start_line: int | None = None
    body_end_line: int | None = None


@dataclass
class ParsedClass:
    name: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    bases: str | None = None
    decorators: str | None = None
    docstring: str | None = None
    is_abstract: bool = False
    interfaces: str | None = None


@dataclass
class ParsedMethod:
    name: str
    class_name: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    parameters: str | None = None
    return_type: str | None = None
    decorators: str | None = None
    is_async: bool = False
    is_static: bool = False
    is_constructor: bool = False
    docstring: str | None = None


@dataclass
class ParsedImport:
    name: str | None
    module: str | None
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    alias: str | None = None
    is_default: bool = False
    is_wildcard: bool = False


@dataclass
class ParsedExport:
    name: str | None
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    is_default: bool = False
    exported_type: str | None = None


@dataclass
class ParsedVariable:
    name: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    var_type: str | None = None
    is_constant: bool = False
    scope: str | None = None
    initial_value: str | None = None


@dataclass
class ParsedComment:
    text: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    comment_type: str | None = None
    is_docstring: bool = False


@dataclass
class ParseResult:
    functions: list[ParsedFunction] = field(default_factory=list)
    classes: list[ParsedClass] = field(default_factory=list)
    methods: list[ParsedMethod] = field(default_factory=list)
    imports: list[ParsedImport] = field(default_factory=list)
    exports: list[ParsedExport] = field(default_factory=list)
    variables: list[ParsedVariable] = field(default_factory=list)
    comments: list[ParsedComment] = field(default_factory=list)
    error: str | None = None

    @property
    def total_nodes(self) -> int:
        return (
            len(self.functions)
            + len(self.classes)
            + len(self.methods)
            + len(self.imports)
            + len(self.exports)
            + len(self.variables)
            + len(self.comments)
        )


class BaseParser(ABC):
    """Abstract base class for all language parsers.

    To add a new language parser:
    1. Subclass BaseParser
    2. Implement language_name property and get_language() method
    3. Override the extraction methods
    4. Register in ParserRouter
    """

    def __init__(self):
        self._parser: Parser | None = None
        self._language: Language | None = None

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the name of the language this parser handles."""
        ...

    @abstractmethod
    def get_language(self) -> Language:
        """Return the tree-sitter Language object."""
        ...

    def _get_parser(self) -> Parser:
        if self._parser is None:
            self._language = self.get_language()
            self._parser = Parser(self._language)
        return self._parser

    def parse(self, source_code: str) -> ParseResult:
        """Parse source code and extract all AST nodes."""
        result = ParseResult()
        try:
            parser = self._get_parser()
            tree = parser.parse(source_code.encode("utf-8"))
            root = tree.root_node

            if root.has_error:
                result.error = "Source code contains syntax errors"

            result.functions = self.extract_functions(root, source_code)
            result.classes = self.extract_classes(root, source_code)
            result.methods = self.extract_methods(root, source_code)
            result.imports = self.extract_imports(root, source_code)
            result.exports = self.extract_exports(root, source_code)
            result.variables = self.extract_variables(root, source_code)
            result.comments = self.extract_comments(root, source_code)

        except Exception as e:
            result.error = f"Parser failure: {str(e)}"

        return result

    def _node_text(self, node: Node, source: str) -> str:
        """Extract text content from a node."""
        return source[node.start_byte:node.end_byte]

    def _find_children_by_type(self, node: Node, *types: str) -> list[Node]:
        """Find all direct children matching given types."""
        return [c for c in node.children if c.type in types]

    def _find_descendants_by_type(self, node: Node, *types: str) -> list[Node]:
        """Recursively find all descendants matching given types."""
        results: list[Node] = []
        for child in node.children:
            if child.type in types:
                results.append(child)
            results.extend(self._find_descendants_by_type(child, *types))
        return results

    @abstractmethod
    def extract_functions(self, root: Node, source: str) -> list[ParsedFunction]:
        ...

    @abstractmethod
    def extract_classes(self, root: Node, source: str) -> list[ParsedClass]:
        ...

    @abstractmethod
    def extract_methods(self, root: Node, source: str) -> list[ParsedMethod]:
        ...

    @abstractmethod
    def extract_imports(self, root: Node, source: str) -> list[ParsedImport]:
        ...

    def extract_exports(self, root: Node, source: str) -> list[ParsedExport]:
        """Default: no exports (Python doesn't have explicit exports)."""
        return []

    @abstractmethod
    def extract_variables(self, root: Node, source: str) -> list[ParsedVariable]:
        ...

    @abstractmethod
    def extract_comments(self, root: Node, source: str) -> list[ParsedComment]:
        ...
