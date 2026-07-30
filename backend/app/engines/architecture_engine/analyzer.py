"""Architecture analyzer — identifies layers, modules, components, dependencies, and violations."""
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger(__name__)

LAYER_KEYWORDS = {
    "api": ["api", "endpoints", "routes", "controllers", "views", "handlers"],
    "service": ["services", "service", "usecases", "use_cases"],
    "engine": ["engines", "engine", "core", "logic"],
    "repository": ["repositories", "repository", "repo", "repos", "dal", "dao"],
    "model": ["models", "model", "entities", "domain"],
    "schema": ["schemas", "schema", "dto", "serializers"],
    "util": ["utils", "util", "helpers", "common", "shared", "lib"],
    "config": ["config", "configuration", "settings"],
    "test": ["tests", "test", "spec", "specs"],
}

LAYER_ORDER = ["api", "service", "engine", "repository", "model", "schema", "util", "config", "test"]


class ArchitectureAnalyzer:
    """Analyzes repository structure to identify architecture components."""

    def analyze_layers(self, files: list[dict]) -> dict:
        """Identify architectural layers from file paths."""
        layers: dict[str, list[str]] = defaultdict(list)
        unassigned: list[str] = []

        for f in files:
            path = f.get("relative_path", "")
            assigned = False
            path_lower = path.lower()
            for layer, keywords in LAYER_KEYWORDS.items():
                for kw in keywords:
                    if f"/{kw}/" in path_lower or path_lower.startswith(f"{kw}/"):
                        layers[layer].append(path)
                        assigned = True
                        break
                if assigned:
                    break
            if not assigned:
                unassigned.append(path)

        return {
            "layers": {k: sorted(v) for k, v in layers.items()},
            "unassigned": sorted(unassigned),
            "layer_count": len(layers),
            "file_count": len(files),
        }

    def analyze_modules(self, files: list[dict]) -> dict:
        """Identify modules (directories) and their contents."""
        modules: dict[str, dict] = {}
        for f in files:
            path = f.get("relative_path", "")
            parts = path.rsplit("/", 1)
            directory = parts[0] if len(parts) > 1 else "."
            if directory not in modules:
                modules[directory] = {"files": [], "languages": set(), "file_count": 0}
            modules[directory]["files"].append(path)
            modules[directory]["file_count"] += 1
            lang = f.get("language")
            if lang:
                modules[directory]["languages"].add(lang)

        # Serialize sets
        for m in modules.values():
            m["languages"] = sorted(m["languages"])

        return {"modules": modules, "module_count": len(modules)}

    def analyze_components(self, files: list[dict], classes: list[dict], functions: list[dict]) -> dict:
        """Identify logical components (groups of related classes/functions)."""
        components: dict[str, dict] = {}
        for cls in classes:
            fp = cls.get("file_path", "")
            parts = fp.rsplit("/", 1)
            module = parts[0] if len(parts) > 1 else "."
            if module not in components:
                components[module] = {"classes": [], "functions": [], "entry_points": [], "services": []}
            components[module]["classes"].append(cls.get("name", ""))
            if "service" in cls.get("name", "").lower():
                components[module]["services"].append(cls.get("name", ""))

        for fn in functions:
            fp = fn.get("file_path", "")
            parts = fp.rsplit("/", 1)
            module = parts[0] if len(parts) > 1 else "."
            if module not in components:
                components[module] = {"classes": [], "functions": [], "entry_points": [], "services": []}
            components[module]["functions"].append(fn.get("name", ""))
            if fn.get("name", "") in ("main", "__main__", "app", "create_app"):
                components[module]["entry_points"].append(fn.get("name", ""))

        return {"components": components, "component_count": len(components)}

    def analyze_dependencies(self, imports: list[dict], files: list[dict]) -> dict:
        """Generate file and module dependency graphs from imports."""
        file_deps: dict[str, list[str]] = defaultdict(list)
        module_deps: dict[str, set] = defaultdict(set)
        all_file_paths = {f.get("relative_path", "") for f in files}

        for imp in imports:
            source = imp.get("file_path", "")
            module = imp.get("module", "")
            if not source or not module:
                continue
            file_deps[source].append(module)

            src_parts = source.rsplit("/", 1)
            src_module = src_parts[0] if len(src_parts) > 1 else "."
            module_deps[src_module].add(module.split(".")[0] if "." in module else module)

        # Serialize sets
        serialized_module_deps = {k: sorted(v) for k, v in module_deps.items()}

        return {
            "file_dependencies": dict(file_deps),
            "module_dependencies": serialized_module_deps,
            "total_imports": len(imports),
        }

    def detect_circular_dependencies(self, file_deps: dict[str, list[str]]) -> list[dict]:
        """Detect circular dependencies in the dependency graph."""
        circular: list[dict] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for dep in file_deps.get(node, []):
                if dep in rec_stack:
                    cycle_start = path.index(dep) if dep in path else -1
                    if cycle_start >= 0:
                        cycle = path[cycle_start:] + [dep]
                        circular.append({
                            "cycle": cycle,
                            "description": f"Circular dependency: {' → '.join(cycle)}",
                        })
                elif dep not in visited:
                    dfs(dep)
            path.pop()
            rec_stack.discard(node)

        for node in file_deps:
            if node not in visited:
                dfs(node)

        return circular

    def detect_layer_violations(self, imports: list[dict], files: list[dict]) -> list[dict]:
        """Detect imports that violate layered architecture conventions."""
        violations: list[dict] = []

        file_layer_map: dict[str, str] = {}
        for f in files:
            path = f.get("relative_path", "").lower()
            for layer, keywords in LAYER_KEYWORDS.items():
                for kw in keywords:
                    if f"/{kw}/" in path or path.startswith(f"{kw}/"):
                        file_layer_map[f.get("relative_path", "")] = layer
                        break

        for imp in imports:
            source = imp.get("file_path", "")
            module = imp.get("module", "")
            src_layer = file_layer_map.get(source)
            if not src_layer:
                continue

            tgt_layer = None
            for layer, keywords in LAYER_KEYWORDS.items():
                for kw in keywords:
                    if kw in module.lower():
                        tgt_layer = layer
                        break
                if tgt_layer:
                    break

            if not tgt_layer or src_layer == tgt_layer:
                continue

            src_idx = LAYER_ORDER.index(src_layer) if src_layer in LAYER_ORDER else -1
            tgt_idx = LAYER_ORDER.index(tgt_layer) if tgt_layer in LAYER_ORDER else -1

            # Lower layers should not import from higher layers
            if src_idx > tgt_idx > -1 and tgt_layer not in ("util", "config", "model", "schema"):
                violations.append({
                    "violation_type": "layer_violation",
                    "severity": "warning",
                    "description": f"Layer violation: {src_layer} layer imports from {tgt_layer} layer",
                    "source_entity": source,
                    "target_entity": module,
                    "source_file": source,
                    "source_layer": src_layer,
                    "target_layer": tgt_layer,
                })

        return violations

    def analyze_call_graph(self, functions: list[dict], methods: list[dict]) -> dict:
        """Build call graph data from parsed functions and methods."""
        nodes: list[dict] = []
        edges: list[dict] = []

        for fn in functions:
            nodes.append({
                "id": f"fn:{fn.get('file_path', '')}:{fn.get('name', '')}",
                "name": fn.get("name", ""),
                "type": "function",
                "file_path": fn.get("file_path", ""),
            })

        for m in methods:
            class_name = m.get("class_name", "")
            nodes.append({
                "id": f"method:{m.get('file_path', '')}:{class_name}.{m.get('name', '')}",
                "name": f"{class_name}.{m.get('name', '')}" if class_name else m.get("name", ""),
                "type": "method",
                "file_path": m.get("file_path", ""),
                "class_name": class_name,
            })

        # Cross-module call edges (heuristic: functions in same module reference each other)
        module_funcs: dict[str, list[str]] = defaultdict(list)
        for fn in functions:
            fp = fn.get("file_path", "")
            parts = fp.rsplit("/", 1)
            module = parts[0] if len(parts) > 1 else "."
            module_funcs[module].append(fn.get("name", ""))

        for module, fns in module_funcs.items():
            for i, src in enumerate(fns):
                for tgt in fns[i + 1:]:
                    edges.append({"source": f"{module}:{src}", "target": f"{module}:{tgt}", "type": "intra_module"})

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def identify_entry_points(self, files: list[dict], functions: list[dict]) -> list[dict]:
        """Identify application entry points."""
        entry_points = []
        entry_file_names = {"main.py", "app.py", "index.py", "index.js", "index.ts", "server.py", "server.js", "manage.py"}
        for f in files:
            fname = f.get("file_name", "").lower()
            if fname in entry_file_names:
                entry_points.append({"type": "file", "name": fname, "path": f.get("relative_path", "")})

        for fn in functions:
            if fn.get("name") in ("main", "__main__", "create_app", "app"):
                entry_points.append({"type": "function", "name": fn.get("name"), "path": fn.get("file_path", "")})

        return entry_points

    def identify_apis(self, files: list[dict], functions: list[dict]) -> list[dict]:
        """Identify API endpoints from file paths and decorators."""
        apis = []
        for f in files:
            path = f.get("relative_path", "").lower()
            if any(kw in path for kw in ["endpoint", "route", "api", "controller", "handler"]):
                apis.append({"type": "file", "name": f.get("file_name", ""), "path": f.get("relative_path", "")})

        for fn in functions:
            decorators = fn.get("decorators", "") or ""
            if any(d in decorators.lower() for d in ["@router", "@app.", "@get", "@post", "@put", "@delete", "@patch"]):
                apis.append({"type": "endpoint", "name": fn.get("name", ""), "path": fn.get("file_path", ""), "decorators": decorators})

        return apis
