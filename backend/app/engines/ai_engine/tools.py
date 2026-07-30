"""ToolExecutor — calls existing AutoDocOps services on behalf of agents."""
from __future__ import annotations
import time
from typing import Any
from sqlalchemy.orm import Session
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """Executes tool calls against existing AutoDocOps services."""

    def __init__(self, db: Session):
        self.db = db
        self._registry: dict[str, callable] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        self._registry = {
            "search_code": self._search_code,
            "get_repository": self._get_repository,
            "get_files": self._get_files,
            "get_functions": self._get_functions,
            "get_classes": self._get_classes,
            "get_imports": self._get_imports,
            "get_documentation": self._get_documentation,
            "generate_documentation": self._generate_documentation,
            "get_architecture": self._get_architecture,
            "get_dependencies": self._get_dependencies,
            "get_callgraph": self._get_callgraph,
            "get_violations": self._get_violations,
            "analyze_impact": self._analyze_impact,
            "get_impact": self._get_impact,
            "get_risk": self._get_risk,
            "get_commits": self._get_commits,
            "get_changes": self._get_changes,
        }

    @property
    def available_tools(self) -> list[str]:
        return sorted(self._registry.keys())

    def execute(self, tool_name: str, **kwargs) -> dict[str, Any]:
        start = time.time()
        if tool_name not in self._registry:
            return {"error": f"Unknown tool: {tool_name}", "status": "error"}
        try:
            result = self._registry[tool_name](**kwargs)
            duration = round(time.time() - start, 3)
            logger.debug(f"Tool {tool_name} executed in {duration}s")
            return {"data": result, "status": "success", "duration": duration}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e), "status": "error"}

    # --- Tool implementations (delegates to existing services) ---

    def _search_code(self, repository_id: int = 0, query: str = "", **kw) -> dict:
        from app.engines.vector_engine.search_service import SimilaritySearchService
        svc = SimilaritySearchService(self.db)
        results = svc.search(repository_id, query, top_k=kw.get("top_k", 10))
        return {"results": [{"entity_name": r.get("entity_name", ""), "score": r.get("score", 0), "file_path": r.get("file_path", "")} for r in results]}

    def _get_repository(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.repository_repo import RepositoryRepository
        repo = RepositoryRepository(self.db).get_repository_by_id(repository_id)
        if not repo:
            return {"error": "Not found"}
        return {"id": repo.id, "name": repo.name, "url": repo.url}

    def _get_files(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.repository_repo import RepositoryRepository
        files = RepositoryRepository(self.db).get_files_by_repository(repository_id)
        return {"files": [{"path": f.relative_path, "language": f.language} for f in files[:50]]}

    def _get_functions(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.parser_repo import ParserRepository
        fns = ParserRepository(self.db).get_functions_by_repository(repository_id)
        return {"functions": [{"name": f.name, "file_path": getattr(f, "file_path", ""), "parameters": f.parameters, "return_type": f.return_type} for f in fns[:50]]}

    def _get_classes(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.parser_repo import ParserRepository
        cls = ParserRepository(self.db).get_classes_by_repository(repository_id)
        return {"classes": [{"name": c.name, "bases": c.bases, "docstring": c.docstring} for c in cls[:50]]}

    def _get_imports(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.parser_repo import ParserRepository
        nodes = ParserRepository(self.db).get_ast_nodes_by_repository(repository_id)
        from app.models.parser import Import
        imps = [n for n in nodes if isinstance(n, Import)]
        return {"imports": [{"name": i.name, "module": getattr(i, "module", "")} for i in imps[:50]]}

    def _get_documentation(self, repository_id: int = 0, doc_type: str | None = None, **kw) -> dict:
        from app.engines.documentation_engine.documentation_service import DocumentationService
        svc = DocumentationService(self.db)
        docs = svc.get_documentation(repository_id, doc_type)
        return {"documents": [{"id": d.id, "title": d.title, "doc_type": d.doc_type, "summary": d.summary} for d in docs[:20]]}

    def _generate_documentation(self, repository_id: int = 0, doc_types: list | None = None, **kw) -> dict:
        from app.engines.documentation_engine.documentation_service import DocumentationService
        svc = DocumentationService(self.db)
        stats = svc.generate_documentation(repository_id, doc_types)
        return stats

    def _get_architecture(self, repository_id: int = 0, **kw) -> dict:
        from app.engines.architecture_engine.architecture_service import ArchitectureService
        svc = ArchitectureService(self.db)
        models = svc.get_architecture(repository_id)
        return {"models": [{"id": m.id, "model_type": m.model_type, "name": m.name} for m in models]}

    def _get_dependencies(self, repository_id: int = 0, **kw) -> dict:
        from app.engines.architecture_engine.architecture_service import ArchitectureService
        return ArchitectureService(self.db).get_dependencies(repository_id) or {}

    def _get_callgraph(self, repository_id: int = 0, **kw) -> dict:
        from app.engines.architecture_engine.architecture_service import ArchitectureService
        return ArchitectureService(self.db).get_callgraph(repository_id) or {}

    def _get_violations(self, repository_id: int = 0, **kw) -> dict:
        from app.engines.architecture_engine.architecture_service import ArchitectureService
        vs = ArchitectureService(self.db).get_violations(repository_id)
        return {"violations": [{"type": v.violation_type, "severity": v.severity, "description": v.description} for v in vs[:20]]}

    def _analyze_impact(self, repository_id: int = 0, **kw) -> dict:
        from app.engines.impact_engine.impact_service import ImpactAnalysisService
        return ImpactAnalysisService(self.db).analyze_impact(repository_id)

    def _get_impact(self, repository_id: int = 0, entity_name: str = "", **kw) -> dict:
        from app.engines.impact_engine.impact_service import ImpactAnalysisService
        svc = ImpactAnalysisService(self.db)
        r = svc.get_entity_impact(repository_id, entity_name)
        if not r:
            return {"error": "Not found"}
        return {"entity_name": r.entity_name, "risk_level": r.risk_level, "risk_score": r.risk_score, "direct_dependents": r.direct_dependents}

    def _get_risk(self, repository_id: int = 0, **kw) -> dict:
        from app.engines.impact_engine.impact_service import ImpactAnalysisService
        r = ImpactAnalysisService(self.db).get_risk_assessment(repository_id)
        if not r:
            return {"error": "Not found"}
        return {"risk_level": r.risk_level, "risk_score": r.risk_score, "summary": r.summary}

    def _get_commits(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.memory_repo import MemoryRepository
        commits = MemoryRepository(self.db).get_commits_by_repository(repository_id, limit=20)
        return {"commits": [{"hash": c.commit_hash, "author": c.author_name, "message": c.message} for c in commits]}

    def _get_changes(self, repository_id: int = 0, **kw) -> dict:
        from app.repositories.memory_repo import MemoryRepository
        mr = MemoryRepository(self.db)
        css = mr.get_change_sets_by_repository(repository_id, limit=1)
        if not css:
            return {"changes": []}
        fcs = mr.get_file_changes_by_change_set(css[0].id)
        return {"changes": [{"file_path": fc.file_path, "change_type": fc.change_type} for fc in fcs[:30]]}
