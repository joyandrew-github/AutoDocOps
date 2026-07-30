"""ArchitectureService — orchestrates incremental architecture analysis and diagram generation."""
import hashlib
import json
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.engines.architecture_engine.analyzer import ArchitectureAnalyzer
from app.engines.architecture_engine.diagram_generator import DiagramGenerator
from app.repositories.architecture_repo import ArchitectureRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.parser_repo import ParserRepository
from app.repositories.memory_repo import MemoryRepository
from app.models.parser import Function, Class, Method, Import
from app.core.logging import get_logger

logger = get_logger(__name__)

MODEL_TYPES = ["layers", "modules", "components", "dependencies", "callgraph", "structure"]
DIAGRAM_FORMATS = ["mermaid", "plantuml", "json", "svg"]


class ArchitectureService:
    """Generates and maintains architecture models and diagrams."""

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = ArchitectureAnalyzer()
        self.diagram_gen = DiagramGenerator()
        self.arch_repo = ArchitectureRepository(db)
        self.repo_repo = RepositoryRepository(db)
        self.parser_repo = ParserRepository(db)
        self.memory_repo = MemoryRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_architecture(self, repository_id: int) -> dict:
        """Full architecture analysis and diagram generation."""
        start = time.time()
        stats = {
            "models_created": 0,
            "models_updated": 0,
            "models_skipped": 0,
            "diagrams_generated": 0,
            "violations_detected": 0,
            "duration_seconds": 0.0,
            "errors": [],
        }

        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        snapshot = self.arch_repo.create_snapshot(repository_id)
        self.arch_repo.update_snapshot(snapshot, status="running", started_at=datetime.now(timezone.utc))

        try:
            files = self.repo_repo.get_files_by_repository(repository_id)
            nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)
            file_map = {f.id: f for f in files}

            file_dicts = [{"relative_path": f.relative_path, "file_name": f.file_name, "language": f.language} for f in files]
            func_dicts = []
            class_dicts = []
            method_dicts = []
            import_dicts = []

            for n in nodes:
                rf = file_map.get(n.file_id)
                fp = rf.relative_path if rf else ""
                if isinstance(n, Function):
                    func_dicts.append({"name": n.name, "file_path": fp, "parameters": n.parameters, "return_type": n.return_type, "decorators": n.decorators, "docstring": n.docstring})
                elif isinstance(n, Class):
                    class_dicts.append({"name": n.name, "file_path": fp, "bases": n.bases, "docstring": n.docstring})
                elif isinstance(n, Method):
                    method_dicts.append({"name": n.name, "file_path": fp, "class_name": getattr(n, "class_name", ""), "parameters": n.parameters, "return_type": n.return_type})
                elif isinstance(n, Import):
                    import_dicts.append({"name": n.name, "file_path": fp, "module": getattr(n, "module", "")})

            # Run analyses
            layers = self.analyzer.analyze_layers(file_dicts)
            modules = self.analyzer.analyze_modules(file_dicts)
            components = self.analyzer.analyze_components(file_dicts, class_dicts, func_dicts)
            dependencies = self.analyzer.analyze_dependencies(import_dicts, file_dicts)
            callgraph = self.analyzer.analyze_call_graph(func_dicts, method_dicts)
            entry_points = self.analyzer.identify_entry_points(file_dicts, func_dicts)
            apis = self.analyzer.identify_apis(file_dicts, func_dicts)

            # Store models
            model_data = {
                "layers": {"data": layers, "name": "Layer Architecture", "desc": "Architectural layer analysis"},
                "modules": {"data": modules, "name": "Module Structure", "desc": "Module and package analysis"},
                "components": {"data": components, "name": "Component Architecture", "desc": "Logical component analysis"},
                "dependencies": {"data": dependencies, "name": "Dependency Graph", "desc": "Module and file dependency analysis"},
                "callgraph": {"data": callgraph, "name": "Call Graph", "desc": "Function and method call graph"},
                "structure": {"data": {"files": file_dicts, "entry_points": entry_points, "apis": apis}, "name": "Repository Structure", "desc": "Repository file structure"},
            }

            for model_type, info in model_data.items():
                try:
                    self._store_model(repository_id, model_type, info["name"], info["desc"], info["data"], stats)
                except Exception as e:
                    logger.error(f"Failed to store model {model_type}: {e}")
                    stats["errors"].append(f"model {model_type}: {e}")

            # Generate diagrams for all models and formats
            diagram_generators = {
                "layers": lambda fmt: self.diagram_gen.generate_layer_diagram(layers, fmt),
                "modules": lambda fmt: self.diagram_gen.generate_package_diagram(modules, fmt),
                "components": lambda fmt: self.diagram_gen.generate_component_diagram(components, fmt),
                "dependencies": lambda fmt: self.diagram_gen.generate_dependency_diagram(dependencies, fmt),
                "callgraph": lambda fmt: self.diagram_gen.generate_callgraph_diagram(callgraph, fmt),
                "structure": lambda fmt: self.diagram_gen.generate_structure_diagram(file_dicts, fmt),
            }

            for model_type, gen_fn in diagram_generators.items():
                model = self.arch_repo.get_model_by_type(repository_id, model_type)
                if not model:
                    continue
                self.arch_repo.delete_diagrams_by_model(model.id)
                for fmt in DIAGRAM_FORMATS:
                    try:
                        content = gen_fn(fmt)
                        self.arch_repo.create_diagram(
                            model_id=model.id,
                            repository_id=repository_id,
                            diagram_type=model_type,
                            title=f"{model.name} ({fmt})",
                            format=fmt,
                            content=content,
                            content_hash=hashlib.sha256(content.encode()).hexdigest(),
                        )
                        stats["diagrams_generated"] += 1
                    except Exception as e:
                        logger.error(f"Failed to generate {fmt} diagram for {model_type}: {e}")
                        stats["errors"].append(f"diagram {model_type}/{fmt}: {e}")

            # Detect violations
            self.arch_repo.delete_violations_by_repository(repository_id)
            violations = []

            circular = self.analyzer.detect_circular_dependencies(dependencies.get("file_dependencies", {}))
            for c in circular:
                violations.append({
                    "repository_id": repository_id,
                    "violation_type": "circular_dependency",
                    "severity": "error",
                    "description": c["description"],
                })

            layer_violations = self.analyzer.detect_layer_violations(import_dicts, file_dicts)
            for lv in layer_violations:
                violations.append({
                    "repository_id": repository_id,
                    "violation_type": lv["violation_type"],
                    "severity": lv["severity"],
                    "description": lv["description"],
                    "source_entity": lv.get("source_entity"),
                    "target_entity": lv.get("target_entity"),
                    "source_file": lv.get("source_file"),
                    "source_layer": lv.get("source_layer"),
                    "target_layer": lv.get("target_layer"),
                })

            if violations:
                self.arch_repo.bulk_create_violations(violations)
            stats["violations_detected"] = len(violations)

            duration = round(time.time() - start, 3)
            stats["duration_seconds"] = duration
            total = stats["models_created"] + stats["models_updated"] + stats["models_skipped"]
            self.arch_repo.update_snapshot(snapshot,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_models=total,
                models_created=stats["models_created"],
                models_updated=stats["models_updated"],
                models_skipped=stats["models_skipped"],
                diagrams_generated=stats["diagrams_generated"],
                violations_detected=stats["violations_detected"],
                duration_seconds=duration,
            )

            logger.info(
                f"Architecture generation completed for repository {repository_id} in {duration}s: "
                f"+{stats['models_created']} created, ~{stats['models_updated']} updated, "
                f"{stats['diagrams_generated']} diagrams, {stats['violations_detected']} violations"
            )

        except Exception as e:
            logger.error(f"Architecture generation failed for repository {repository_id}: {e}")
            self.arch_repo.update_snapshot(snapshot,
                status="failed", error_message=str(e), completed_at=datetime.now(timezone.utc),
            )
            stats["errors"].append(str(e))

        return stats

    def get_architecture(self, repository_id: int) -> list:
        return self.arch_repo.get_models_by_repository(repository_id)

    def get_architecture_by_id(self, model_id: int):
        return self.arch_repo.get_model_by_id(model_id)

    def get_dependencies(self, repository_id: int) -> dict | None:
        model = self.arch_repo.get_model_by_type(repository_id, "dependencies")
        return model.data if model else None

    def get_callgraph(self, repository_id: int) -> dict | None:
        model = self.arch_repo.get_model_by_type(repository_id, "callgraph")
        return model.data if model else None

    def get_violations(self, repository_id: int, resolved: bool | None = None) -> list:
        return self.arch_repo.get_violations_by_repository(repository_id, resolved)

    def get_diagrams(self, repository_id: int, diagram_type: str | None = None, format: str | None = None) -> list:
        diagrams = self.arch_repo.get_diagrams_by_repository(repository_id, diagram_type)
        if format:
            diagrams = [d for d in diagrams if d.format == format]
        return diagrams

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _store_model(self, repository_id: int, model_type: str, name: str, desc: str, data: dict, stats: dict) -> None:
        content_hash = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        existing = self.arch_repo.get_model_by_type(repository_id, model_type)

        if existing:
            if existing.content_hash == content_hash:
                stats["models_skipped"] += 1
                return
            self.arch_repo.update_model(existing,
                data=data, content_hash=content_hash, version=existing.version + 1, description=desc,
            )
            stats["models_updated"] += 1
        else:
            self.arch_repo.create_model(
                repository_id=repository_id, model_type=model_type,
                name=name, description=desc, data=data, content_hash=content_hash,
            )
            stats["models_created"] += 1
