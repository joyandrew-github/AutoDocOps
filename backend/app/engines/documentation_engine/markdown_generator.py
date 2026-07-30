"""Markdown generator — builds structured documentation from code entities."""
from app.core.logging import get_logger

logger = get_logger(__name__)


class MarkdownGenerator:
    """Generates Markdown documentation from parsed code data."""

    # ------------------------------------------------------------------
    # Repository-level docs
    # ------------------------------------------------------------------

    def generate_repository_overview(
        self,
        repo_name: str,
        description: str | None,
        languages: list[dict],
        frameworks: list[dict],
        dependencies: list[dict],
        file_count: int,
        class_count: int,
        function_count: int,
    ) -> tuple[str, str, list[dict]]:
        """Generate repository overview. Returns (content, summary, sections)."""
        sections = []
        parts = [f"# {repo_name}\n"]

        summary = description or f"Documentation for {repo_name}."
        parts.append(f"{summary}\n")

        # Stats
        stats = (
            f"## Project Statistics\n\n"
            f"| Metric | Value |\n|--------|-------|\n"
            f"| Files | {file_count} |\n"
            f"| Classes | {class_count} |\n"
            f"| Functions | {function_count} |\n"
        )
        parts.append(stats)
        sections.append({"title": "Project Statistics", "content": stats, "section_order": 0, "section_type": "statistics", "level": 2})

        # Languages
        if languages:
            lang_md = "## Programming Languages\n\n| Language | Files | Percentage |\n|----------|-------|------------|\n"
            for lang in languages:
                lang_md += f"| {lang.get('name', '')} | {lang.get('file_count', 0)} | {lang.get('percentage', 0):.1f}% |\n"
            parts.append(lang_md)
            sections.append({"title": "Programming Languages", "content": lang_md, "section_order": 1, "section_type": "languages", "level": 2})

        # Frameworks
        if frameworks:
            fw_md = "## Frameworks\n\n| Framework | Version |\n|-----------|--------|\n"
            for fw in frameworks:
                fw_md += f"| {fw.get('name', '')} | {fw.get('version', 'N/A')} |\n"
            parts.append(fw_md)
            sections.append({"title": "Frameworks", "content": fw_md, "section_order": 2, "section_type": "frameworks", "level": 2})

        # Dependencies
        if dependencies:
            dep_md = "## Dependencies\n\n| Name | Version | Package Manager |\n|------|---------|----------------|\n"
            for dep in dependencies:
                dep_md += f"| {dep.get('name', '')} | {dep.get('version', 'N/A')} | {dep.get('package_manager', '')} |\n"
            parts.append(dep_md)
            sections.append({"title": "Dependencies", "content": dep_md, "section_order": 3, "section_type": "dependencies", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # File-level docs
    # ------------------------------------------------------------------

    def generate_file_documentation(
        self,
        file_path: str,
        language: str | None,
        classes: list[dict],
        functions: list[dict],
        imports: list[dict],
        variables: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate file documentation. Returns (content, summary, sections)."""
        sections = []
        file_name = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
        parts = [f"# {file_name}\n"]

        summary_parts = []
        if language:
            summary_parts.append(f"**Language:** {language}")
        summary_parts.append(f"**Path:** `{file_path}`")
        if classes:
            summary_parts.append(f"**Classes:** {len(classes)}")
        if functions:
            summary_parts.append(f"**Functions:** {len(functions)}")

        summary = f"{file_name} — {language or 'Unknown'} file with {len(classes)} classes and {len(functions)} functions."
        parts.append(" | ".join(summary_parts) + "\n")

        # Table of Contents
        if classes or functions:
            toc = "## Table of Contents\n\n"
            for cls in classes:
                toc += f"- [{cls.get('name', '')}](#{cls.get('name', '').lower().replace(' ', '-')})\n"
            for fn in functions:
                toc += f"- [{fn.get('name', '')}](#{fn.get('name', '').lower().replace(' ', '-')})\n"
            parts.append(toc)
            sections.append({"title": "Table of Contents", "content": toc, "section_order": 0, "section_type": "toc", "level": 2})

        # Imports
        if imports:
            imp_md = "## Imports\n\n"
            for imp in imports:
                module = imp.get("module", "")
                name = imp.get("name", "")
                imp_md += f"- `{module}`" + (f" ({name})" if name else "") + "\n"
            parts.append(imp_md)
            sections.append({"title": "Imports", "content": imp_md, "section_order": 1, "section_type": "imports", "level": 2})

        # Classes
        for i, cls in enumerate(classes):
            cls_md = self._generate_class_section(cls)
            parts.append(cls_md)
            sections.append({"title": cls.get("name", "Class"), "content": cls_md, "section_order": 2 + i, "section_type": "class", "level": 2})

        # Functions
        for i, fn in enumerate(functions):
            fn_md = self._generate_function_section(fn)
            parts.append(fn_md)
            sections.append({"title": fn.get("name", "Function"), "content": fn_md, "section_order": 2 + len(classes) + i, "section_type": "function", "level": 2})

        # Variables
        if variables:
            var_md = "## Variables\n\n| Name | Type | Constant |\n|------|------|----------|\n"
            for var in variables:
                var_md += f"| `{var.get('name', '')}` | `{var.get('var_type', 'unknown')}` | {'Yes' if var.get('is_constant') else 'No'} |\n"
            parts.append(var_md)
            sections.append({"title": "Variables", "content": var_md, "section_order": 100, "section_type": "variables", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Class documentation
    # ------------------------------------------------------------------

    def generate_class_documentation(
        self,
        class_data: dict,
        methods: list[dict],
        file_path: str | None = None,
    ) -> tuple[str, str, list[dict]]:
        """Generate standalone class documentation."""
        sections = []
        name = class_data.get("name", "Class")
        parts = [f"# Class: {name}\n"]

        summary = f"Class `{name}`"
        if class_data.get("bases"):
            summary += f" extends `{class_data['bases']}`"
        summary += "."

        if file_path:
            parts.append(f"**File:** `{file_path}`\n")
        if class_data.get("bases"):
            parts.append(f"**Extends:** `{class_data['bases']}`\n")
        if class_data.get("docstring"):
            parts.append(f"## Description\n\n{class_data['docstring']}\n")
            sections.append({"title": "Description", "content": class_data["docstring"], "section_order": 0, "section_type": "description", "level": 2})

        if methods:
            meth_md = "## Methods\n\n"
            for m in methods:
                meth_md += self._generate_method_entry(m)
            parts.append(meth_md)
            sections.append({"title": "Methods", "content": meth_md, "section_order": 1, "section_type": "methods", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Function documentation
    # ------------------------------------------------------------------

    def generate_function_documentation(
        self,
        func_data: dict,
        file_path: str | None = None,
    ) -> tuple[str, str, list[dict]]:
        """Generate standalone function documentation."""
        sections = []
        name = func_data.get("name", "function")
        parts = [f"# Function: {name}\n"]

        sig = f"def {name}({func_data.get('parameters', '')})"
        if func_data.get("return_type"):
            sig += f" -> {func_data['return_type']}"

        summary = f"Function `{name}`"
        if func_data.get("return_type"):
            summary += f" returning `{func_data['return_type']}`"
        summary += "."

        parts.append(f"```python\n{sig}\n```\n")
        sections.append({"title": "Signature", "content": sig, "section_order": 0, "section_type": "signature", "level": 2})

        if file_path:
            parts.append(f"**File:** `{file_path}`\n")

        if func_data.get("docstring"):
            parts.append(f"## Description\n\n{func_data['docstring']}\n")
            sections.append({"title": "Description", "content": func_data["docstring"], "section_order": 1, "section_type": "description", "level": 2})

        if func_data.get("parameters"):
            parts.append(f"## Parameters\n\n`{func_data['parameters']}`\n")
            sections.append({"title": "Parameters", "content": func_data["parameters"], "section_order": 2, "section_type": "parameters", "level": 2})

        if func_data.get("return_type"):
            parts.append(f"## Returns\n\n`{func_data['return_type']}`\n")
            sections.append({"title": "Returns", "content": func_data["return_type"], "section_order": 3, "section_type": "returns", "level": 2})

        if func_data.get("decorators"):
            parts.append(f"## Decorators\n\n`{func_data['decorators']}`\n")
            sections.append({"title": "Decorators", "content": func_data["decorators"], "section_order": 4, "section_type": "decorators", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Module / folder / package docs
    # ------------------------------------------------------------------

    def generate_module_documentation(
        self,
        module_path: str,
        files: list[dict],
        classes: list[dict],
        functions: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate module/folder documentation."""
        sections = []
        module_name = module_path.rsplit("/", 1)[-1] if "/" in module_path else module_path
        parts = [f"# Module: {module_name}\n"]

        summary = f"Module `{module_name}` with {len(files)} files, {len(classes)} classes, {len(functions)} functions."
        parts.append(f"**Path:** `{module_path}`\n")

        if files:
            file_md = "## Files\n\n| File | Language |\n|------|----------|\n"
            for f in files:
                file_md += f"| `{f.get('file_name', '')}` | {f.get('language', 'Unknown')} |\n"
            parts.append(file_md)
            sections.append({"title": "Files", "content": file_md, "section_order": 0, "section_type": "files", "level": 2})

        if classes:
            cls_md = "## Classes\n\n"
            for c in classes:
                cls_md += f"- **{c.get('name', '')}**"
                if c.get("bases"):
                    cls_md += f" (extends `{c['bases']}`)"
                cls_md += "\n"
            parts.append(cls_md)
            sections.append({"title": "Classes", "content": cls_md, "section_order": 1, "section_type": "classes", "level": 2})

        if functions:
            fn_md = "## Functions\n\n"
            for f in functions:
                fn_md += f"- **{f.get('name', '')}**(`{f.get('parameters', '')}`)"
                if f.get("return_type"):
                    fn_md += f" → `{f['return_type']}`"
                fn_md += "\n"
            parts.append(fn_md)
            sections.append({"title": "Functions", "content": fn_md, "section_order": 2, "section_type": "functions", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Change log / commit history
    # ------------------------------------------------------------------

    def generate_changelog(
        self,
        repo_name: str,
        commits: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate a changelog from commit history."""
        sections = []
        parts = [f"# Changelog — {repo_name}\n"]
        summary = f"Changelog with {len(commits)} commits."

        if commits:
            commit_md = "## Recent Commits\n\n| Hash | Author | Date | Message |\n|------|--------|------|---------|\n"
            for c in commits:
                short_hash = c.get("commit_hash", "")[:8]
                commit_md += (
                    f"| `{short_hash}` | {c.get('author_name', 'Unknown')} "
                    f"| {c.get('committed_at', '')} | {c.get('message', '')[:80]} |\n"
                )
            parts.append(commit_md)
            sections.append({"title": "Recent Commits", "content": commit_md, "section_order": 0, "section_type": "commits", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Onboarding guide
    # ------------------------------------------------------------------

    def generate_onboarding_guide(
        self,
        repo_name: str,
        description: str | None,
        languages: list[dict],
        frameworks: list[dict],
        key_files: list[dict],
    ) -> tuple[str, str, list[dict]]:
        """Generate a developer onboarding guide."""
        sections = []
        parts = [f"# Developer Onboarding — {repo_name}\n"]
        summary = f"Onboarding guide for {repo_name}."

        if description:
            parts.append(f"## Overview\n\n{description}\n")
            sections.append({"title": "Overview", "content": description, "section_order": 0, "section_type": "overview", "level": 2})

        if languages:
            lang_names = ", ".join(l.get("name", "") for l in languages[:5])
            tech_md = f"## Tech Stack\n\n**Languages:** {lang_names}\n"
            if frameworks:
                fw_names = ", ".join(f.get("name", "") for f in frameworks[:5])
                tech_md += f"\n**Frameworks:** {fw_names}\n"
            parts.append(tech_md)
            sections.append({"title": "Tech Stack", "content": tech_md, "section_order": 1, "section_type": "tech_stack", "level": 2})

        if key_files:
            files_md = "## Key Files\n\n"
            for f in key_files[:20]:
                files_md += f"- `{f.get('relative_path', f.get('file_name', ''))}`\n"
            parts.append(files_md)
            sections.append({"title": "Key Files", "content": files_md, "section_order": 2, "section_type": "key_files", "level": 2})

        parts.append("## Getting Started\n\n1. Clone the repository\n2. Install dependencies\n3. Review the key files above\n4. Run the test suite\n")
        sections.append({"title": "Getting Started", "content": parts[-1], "section_order": 3, "section_type": "getting_started", "level": 2})

        content = "\n".join(parts)
        return content, summary, sections

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def to_html(self, markdown_content: str) -> str:
        """Convert markdown to simple HTML."""
        lines = markdown_content.split("\n")
        html_parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{font-family:sans-serif;max-width:900px;margin:0 auto;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f4f4f4}code{background:#f0f0f0;padding:2px 4px;border-radius:3px}pre{background:#f0f0f0;padding:12px;border-radius:4px;overflow-x:auto}</style></head><body>"]
        in_code_block = False
        in_table = False

        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    html_parts.append("</code></pre>")
                    in_code_block = False
                else:
                    html_parts.append("<pre><code>")
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(line)
                continue

            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("| ") and not in_table:
                in_table = True
                html_parts.append("<table>")
                cells = [c.strip() for c in line.split("|")[1:-1]]
                html_parts.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            elif line.startswith("|---") or line.startswith("| ---"):
                continue  # table separator
            elif line.startswith("| ") and in_table:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            elif in_table and not line.startswith("|"):
                html_parts.append("</table>")
                in_table = False
                html_parts.append(f"<p>{line}</p>" if line.strip() else "")
            elif line.startswith("- "):
                html_parts.append(f"<li>{line[2:]}</li>")
            elif line.strip():
                html_parts.append(f"<p>{line}</p>")

        if in_table:
            html_parts.append("</table>")
        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    def to_pdf_ready_markdown(self, markdown_content: str, title: str) -> str:
        """Wrap markdown with PDF-ready metadata header."""
        header = (
            "---\n"
            f"title: \"{title}\"\n"
            f"output: pdf_document\n"
            "geometry: margin=1in\n"
            "fontsize: 11pt\n"
            "---\n\n"
        )
        return header + markdown_content

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_class_section(self, cls: dict) -> str:
        name = cls.get("name", "Class")
        parts = [f"## {name}\n"]
        if cls.get("bases"):
            parts.append(f"**Extends:** `{cls['bases']}`\n")
        if cls.get("docstring"):
            parts.append(f"{cls['docstring']}\n")
        return "\n".join(parts)

    def _generate_function_section(self, fn: dict) -> str:
        name = fn.get("name", "function")
        parts = [f"## {name}\n"]
        sig = f"def {name}({fn.get('parameters', '')})"
        if fn.get("return_type"):
            sig += f" -> {fn['return_type']}"
        parts.append(f"```python\n{sig}\n```\n")
        if fn.get("docstring"):
            parts.append(f"{fn['docstring']}\n")
        return "\n".join(parts)

    def _generate_method_entry(self, m: dict) -> str:
        name = m.get("name", "method")
        sig = f"def {name}({m.get('parameters', '')})"
        if m.get("return_type"):
            sig += f" -> {m['return_type']}"
        entry = f"### {name}\n\n```python\n{sig}\n```\n"
        if m.get("docstring"):
            entry += f"\n{m['docstring']}\n"
        return entry + "\n"
