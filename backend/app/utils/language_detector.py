class LanguageDetector:
    """Detects programming language from file extension."""

    EXTENSION_MAP: dict[str, str] = {
        ".py": "Python",
        ".java": "Java",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".c": "C",
        ".h": "C",
        ".cpp": "C++",
        ".cxx": "C++",
        ".cc": "C++",
        ".hpp": "C++",
        ".cs": "C#",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".xml": "XML",
        ".md": "Markdown",
        ".markdown": "Markdown",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".hcl": "Terraform",
        ".tf": "Terraform",
    }

    FILENAME_MAP: dict[str, str] = {
        "Dockerfile": "Dockerfile",
        "Makefile": "Shell",
        "Jenkinsfile": "Groovy",
    }

    def detect(self, file_name: str, extension: str | None) -> str | None:
        """Detect programming language from file name or extension."""
        if file_name in self.FILENAME_MAP:
            return self.FILENAME_MAP[file_name]

        if extension and extension in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[extension]

        return None

    def get_supported_languages(self) -> list[str]:
        """Return list of all supported languages."""
        return sorted(set(self.EXTENSION_MAP.values()) | set(self.FILENAME_MAP.values()))
