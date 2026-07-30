"""Diagram generator — exports architecture models to PlantUML, Mermaid, JSON, SVG-ready."""
import json
from app.core.logging import get_logger

logger = get_logger(__name__)


class DiagramGenerator:
    """Generates exportable diagram definitions from architecture data."""

    # ------------------------------------------------------------------
    # Component diagram
    # ------------------------------------------------------------------

    def generate_component_diagram(self, components: dict, format: str = "mermaid") -> str:
        if format == "plantuml":
            return self._component_plantuml(components)
        elif format == "json":
            return json.dumps(components, indent=2, default=str)
        elif format == "svg":
            return self._component_svg(components)
        return self._component_mermaid(components)

    def _component_mermaid(self, components: dict) -> str:
        lines = ["graph TD"]
        comps = components.get("components", {})
        for name, data in comps.items():
            safe = name.replace("/", "_").replace(".", "_").replace("-", "_")
            classes = data.get("classes", [])
            label = f"{name}\\n({len(classes)} classes)"
            lines.append(f"    {safe}[\"{label}\"]")
        return "\n".join(lines)

    def _component_plantuml(self, components: dict) -> str:
        lines = ["@startuml", "skinparam componentStyle rectangle"]
        comps = components.get("components", {})
        for name, data in comps.items():
            safe = name.replace("/", ".").replace("-", "_")
            classes = data.get("classes", [])
            lines.append(f'component "{name}" as {safe.replace(".", "_")} {{')
            for cls in classes[:10]:
                lines.append(f"    [{cls}]")
            lines.append("}")
        lines.append("@enduml")
        return "\n".join(lines)

    def _component_svg(self, components: dict) -> str:
        comps = list(components.get("components", {}).items())
        width = max(300, len(comps) * 200)
        height = 200
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        for i, (name, data) in enumerate(comps[:20]):
            x = 20 + i * 180
            y = 30
            cls_count = len(data.get("classes", []))
            parts.append(f'<rect x="{x}" y="{y}" width="160" height="80" rx="8" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>')
            parts.append(f'<text x="{x+80}" y="{y+35}" text-anchor="middle" font-size="12" fill="#333">{name[-20:]}</text>')
            parts.append(f'<text x="{x+80}" y="{y+55}" text-anchor="middle" font-size="10" fill="#666">{cls_count} classes</text>')
        parts.append("</svg>")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Package diagram
    # ------------------------------------------------------------------

    def generate_package_diagram(self, modules: dict, format: str = "mermaid") -> str:
        if format == "plantuml":
            return self._package_plantuml(modules)
        elif format == "json":
            return json.dumps(modules, indent=2, default=str)
        elif format == "svg":
            return self._package_svg(modules)
        return self._package_mermaid(modules)

    def _package_mermaid(self, modules: dict) -> str:
        lines = ["graph TD"]
        mods = modules.get("modules", {})
        for name, data in mods.items():
            safe = name.replace("/", "_").replace(".", "_").replace("-", "_")
            fc = data.get("file_count", 0)
            lines.append(f"    {safe}[\"{name}\\n({fc} files)\"]")
        return "\n".join(lines)

    def _package_plantuml(self, modules: dict) -> str:
        lines = ["@startuml"]
        mods = modules.get("modules", {})
        for name, data in mods.items():
            safe = name.replace("/", ".").replace("-", "_")
            fc = data.get("file_count", 0)
            lines.append(f'package "{name}" as {safe.replace(".", "_")} {{')
            lines.append(f"    note: {fc} files")
            lines.append("}")
        lines.append("@enduml")
        return "\n".join(lines)

    def _package_svg(self, modules: dict) -> str:
        mods = list(modules.get("modules", {}).items())
        width = max(300, len(mods) * 180)
        height = 200
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        for i, (name, data) in enumerate(mods[:20]):
            x = 20 + i * 170
            fc = data.get("file_count", 0)
            parts.append(f'<rect x="{x}" y="30" width="150" height="70" rx="6" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>')
            parts.append(f'<text x="{x+75}" y="60" text-anchor="middle" font-size="11" fill="#333">{name[-18:]}</text>')
            parts.append(f'<text x="{x+75}" y="80" text-anchor="middle" font-size="10" fill="#666">{fc} files</text>')
        parts.append("</svg>")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer diagram
    # ------------------------------------------------------------------

    def generate_layer_diagram(self, layers: dict, format: str = "mermaid") -> str:
        if format == "plantuml":
            return self._layer_plantuml(layers)
        elif format == "json":
            return json.dumps(layers, indent=2, default=str)
        elif format == "svg":
            return self._layer_svg(layers)
        return self._layer_mermaid(layers)

    def _layer_mermaid(self, layers: dict) -> str:
        lines = ["graph TB"]
        layer_data = layers.get("layers", {})
        prev = None
        for layer_name in ["api", "service", "engine", "repository", "model", "schema", "util", "config"]:
            if layer_name in layer_data:
                safe = layer_name
                fc = len(layer_data[layer_name])
                lines.append(f"    {safe}[\"{layer_name.upper()}\\n({fc} files)\"]")
                if prev:
                    lines.append(f"    {prev} --> {safe}")
                prev = safe
        return "\n".join(lines)

    def _layer_plantuml(self, layers: dict) -> str:
        lines = ["@startuml"]
        layer_data = layers.get("layers", {})
        for layer_name in ["api", "service", "engine", "repository", "model", "schema", "util", "config"]:
            if layer_name in layer_data:
                fc = len(layer_data[layer_name])
                lines.append(f'rectangle "{layer_name.upper()} ({fc} files)" as {layer_name}')
        prev = None
        for layer_name in ["api", "service", "engine", "repository", "model"]:
            if layer_name in layer_data:
                if prev:
                    lines.append(f"{prev} --> {layer_name}")
                prev = layer_name
        lines.append("@enduml")
        return "\n".join(lines)

    def _layer_svg(self, layers: dict) -> str:
        layer_data = layers.get("layers", {})
        ordered = [l for l in ["api", "service", "engine", "repository", "model", "schema", "util", "config"] if l in layer_data]
        height = max(200, len(ordered) * 60 + 40)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}">']
        colors = ["#e8eaf6", "#c5cae9", "#9fa8da", "#7986cb", "#5c6bc0", "#3f51b5", "#303f9f", "#1a237e"]
        for i, layer in enumerate(ordered):
            y = 20 + i * 55
            fc = len(layer_data[layer])
            color = colors[i % len(colors)]
            parts.append(f'<rect x="50" y="{y}" width="300" height="45" rx="6" fill="{color}" stroke="#333" stroke-width="1"/>')
            parts.append(f'<text x="200" y="{y+28}" text-anchor="middle" font-size="13" fill="#fff" font-weight="bold">{layer.upper()} ({fc} files)</text>')
        parts.append("</svg>")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Dependency diagram
    # ------------------------------------------------------------------

    def generate_dependency_diagram(self, deps: dict, format: str = "mermaid") -> str:
        if format == "plantuml":
            return self._dep_plantuml(deps)
        elif format == "json":
            return json.dumps(deps, indent=2, default=str)
        elif format == "svg":
            return self._dep_svg(deps)
        return self._dep_mermaid(deps)

    def _dep_mermaid(self, deps: dict) -> str:
        lines = ["graph LR"]
        mod_deps = deps.get("module_dependencies", {})
        seen = set()
        for src, targets in mod_deps.items():
            safe_src = src.replace("/", "_").replace(".", "_").replace("-", "_")
            lines.append(f"    {safe_src}[\"{src}\"]")
            for tgt in targets[:10]:
                safe_tgt = tgt.replace("/", "_").replace(".", "_").replace("-", "_")
                edge = f"{safe_src}-->{safe_tgt}"
                if edge not in seen:
                    if safe_tgt not in [l.split("[")[0].strip() for l in lines if "[" in l]:
                        lines.append(f"    {safe_tgt}[\"{tgt}\"]")
                    lines.append(f"    {safe_src} --> {safe_tgt}")
                    seen.add(edge)
        return "\n".join(lines)

    def _dep_plantuml(self, deps: dict) -> str:
        lines = ["@startuml"]
        mod_deps = deps.get("module_dependencies", {})
        for src, targets in mod_deps.items():
            safe_src = src.replace("/", "_").replace(".", "_").replace("-", "_")
            for tgt in targets[:10]:
                safe_tgt = tgt.replace("/", "_").replace(".", "_").replace("-", "_")
                lines.append(f"[{safe_src}] --> [{safe_tgt}]")
        lines.append("@enduml")
        return "\n".join(lines)

    def _dep_svg(self, deps: dict) -> str:
        mod_deps = deps.get("module_dependencies", {})
        modules = list(mod_deps.keys())[:15]
        width = max(400, len(modules) * 150)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="200">']
        for i, mod in enumerate(modules):
            x = 20 + i * 140
            parts.append(f'<rect x="{x}" y="60" width="120" height="40" rx="6" fill="#e8f5e9" stroke="#388e3c" stroke-width="2"/>')
            parts.append(f'<text x="{x+60}" y="85" text-anchor="middle" font-size="10" fill="#333">{mod[-15:]}</text>')
        parts.append("</svg>")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Call graph diagram
    # ------------------------------------------------------------------

    def generate_callgraph_diagram(self, callgraph: dict, format: str = "mermaid") -> str:
        if format == "plantuml":
            return self._callgraph_plantuml(callgraph)
        elif format == "json":
            return json.dumps(callgraph, indent=2, default=str)
        elif format == "svg":
            return self._callgraph_svg(callgraph)
        return self._callgraph_mermaid(callgraph)

    def _callgraph_mermaid(self, callgraph: dict) -> str:
        lines = ["graph LR"]
        nodes = callgraph.get("nodes", [])
        edges = callgraph.get("edges", [])
        seen_nodes = set()
        for n in nodes[:50]:
            nid = n.get("id", "").replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
            if nid and nid not in seen_nodes:
                lines.append(f"    {nid}[\"{n.get('name', '')}\"]")
                seen_nodes.add(nid)
        for e in edges[:50]:
            src = e.get("source", "").replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
            tgt = e.get("target", "").replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
            if src and tgt:
                lines.append(f"    {src} --> {tgt}")
        return "\n".join(lines)

    def _callgraph_plantuml(self, callgraph: dict) -> str:
        lines = ["@startuml"]
        edges = callgraph.get("edges", [])
        for e in edges[:50]:
            src = e.get("source", "").replace(":", "_").replace("/", "_")
            tgt = e.get("target", "").replace(":", "_").replace("/", "_")
            lines.append(f"({src}) --> ({tgt})")
        lines.append("@enduml")
        return "\n".join(lines)

    def _callgraph_svg(self, callgraph: dict) -> str:
        nodes = callgraph.get("nodes", [])[:20]
        width = max(400, len(nodes) * 130)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="150">']
        for i, n in enumerate(nodes):
            x = 20 + i * 120
            parts.append(f'<ellipse cx="{x+50}" cy="75" rx="50" ry="25" fill="#fce4ec" stroke="#c62828" stroke-width="1.5"/>')
            parts.append(f'<text x="{x+50}" y="80" text-anchor="middle" font-size="10" fill="#333">{n.get("name", "")[:12]}</text>')
        parts.append("</svg>")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Structure diagram
    # ------------------------------------------------------------------

    def generate_structure_diagram(self, files: list[dict], format: str = "mermaid") -> str:
        if format == "json":
            return json.dumps({"files": files}, indent=2, default=str)
        tree: dict = {}
        for f in files:
            parts = f.get("relative_path", "").split("/")
            node = tree
            for p in parts:
                node = node.setdefault(p, {})

        if format == "plantuml":
            lines = ["@startsalt", "{"]
            self._tree_plantuml(tree, lines, 1)
            lines.append("}")
            lines.append("@endsalt")
            return "\n".join(lines)
        elif format == "svg":
            return self._structure_svg(tree)

        # Default mermaid
        lines = ["graph TD"]
        self._tree_mermaid(tree, lines, "root", "Repository")
        return "\n".join(lines)

    def _tree_mermaid(self, tree: dict, lines: list, parent_id: str, parent_label: str) -> None:
        lines.append(f"    {parent_id}[\"{parent_label}\"]")
        for key, subtree in list(tree.items())[:20]:
            child_id = f"{parent_id}_{key.replace('.', '_').replace('-', '_')}"
            lines.append(f"    {parent_id} --> {child_id}")
            if subtree:
                self._tree_mermaid(subtree, lines, child_id, key)
            else:
                lines.append(f"    {child_id}[\"{key}\"]")

    def _tree_plantuml(self, tree: dict, lines: list, depth: int) -> None:
        for key, subtree in tree.items():
            prefix = "  " * depth
            if subtree:
                lines.append(f"{prefix}{{T")
                lines.append(f"{prefix}  {key}")
                self._tree_plantuml(subtree, lines, depth + 1)
                lines.append(f"{prefix}}}")
            else:
                lines.append(f"{prefix}  {key}")

    def _structure_svg(self, tree: dict) -> str:
        items = list(tree.keys())[:20]
        height = max(200, len(items) * 25 + 60)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}">']
        parts.append('<text x="20" y="25" font-size="14" font-weight="bold" fill="#333">Repository Structure</text>')
        for i, item in enumerate(items):
            y = 50 + i * 22
            parts.append(f'<text x="30" y="{y}" font-size="11" fill="#555">📁 {item}</text>')
        parts.append("</svg>")
        return "\n".join(parts)
