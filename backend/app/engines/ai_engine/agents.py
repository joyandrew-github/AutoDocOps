"""Specialized agents that consume existing AutoDocOps services."""
from __future__ import annotations
import time
import json
from typing import Generator
from app.engines.ai_engine.base import BaseAgent, AgentContext, AgentResponse
from app.engines.ai_engine.tools import ToolExecutor
from app.core.logging import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# 1. Repository Expert
# ------------------------------------------------------------------

class RepositoryExpert(BaseAgent):
    name = "repository_expert"
    description = "Answers repository questions using vector search and repository memory."
    capabilities = ["repository", "repo", "project", "overview", "files", "languages", "commits", "history"]

    def __init__(self, db=None):
        super().__init__(db)
        self.tools = ToolExecutor(db) if db else None

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        parts = []
        tool_calls = []

        if not context.repository_id:
            return AgentResponse(agent_name=self.name, content="Please specify a repository.", status="error")

        repo = self._call("get_repository", tool_calls, repository_id=context.repository_id)
        parts.append(f"**Repository:** {repo.get('name', 'Unknown')}")

        files = self._call("get_files", tool_calls, repository_id=context.repository_id)
        parts.append(f"**Files:** {len(files.get('files', []))} files found")

        msg = context.user_message.lower()
        if any(kw in msg for kw in ["commit", "history", "change"]):
            commits = self._call("get_commits", tool_calls, repository_id=context.repository_id)
            c_list = commits.get("commits", [])
            parts.append(f"**Recent commits:** {len(c_list)}")
            for c in c_list[:5]:
                parts.append(f"  - `{c.get('hash', '')[:8]}` {c.get('message', '')[:60]}")

        if any(kw in msg for kw in ["search", "find", "look"]):
            search = self._call("search_code", tool_calls, repository_id=context.repository_id, query=context.user_message)
            results = search.get("results", [])
            if results:
                parts.append(f"**Search results:** {len(results)} matches")
                for r in results[:5]:
                    parts.append(f"  - `{r.get('entity_name', '')}` ({r.get('file_path', '')})")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            tool_calls=tool_calls, duration_seconds=round(time.time() - start, 3),
        )

    def _call(self, tool: str, tool_calls: list, **kwargs) -> dict:
        if not self.tools:
            return {}
        result = self.tools.execute(tool, **kwargs)
        tool_calls.append({"tool": tool, "status": result.get("status")})
        return result.get("data", {}) if result.get("status") == "success" else {}

    def can_handle(self, message: str) -> float:
        score = super().can_handle(message)
        msg = message.lower()
        if any(kw in msg for kw in ["repository", "repo", "project", "overview"]):
            score = max(score, 0.8)
        return score


# ------------------------------------------------------------------
# 2. Code Expert
# ------------------------------------------------------------------

class CodeExpert(BaseAgent):
    name = "code_expert"
    description = "Explains functions, classes, modules, and APIs using parser and knowledge graph."
    capabilities = ["function", "class", "method", "module", "code", "explain", "parameter", "return", "api"]

    def __init__(self, db=None):
        super().__init__(db)
        self.tools = ToolExecutor(db) if db else None

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        parts = []
        tool_calls = []

        if not context.repository_id:
            return AgentResponse(agent_name=self.name, content="Please specify a repository.", status="error")

        msg = context.user_message.lower()

        if any(kw in msg for kw in ["class", "classes"]):
            classes = self._call("get_classes", tool_calls, repository_id=context.repository_id)
            cls_list = classes.get("classes", [])
            parts.append(f"**Classes:** {len(cls_list)} found")
            for c in cls_list[:10]:
                bases = f" (extends {c.get('bases', '')})" if c.get("bases") else ""
                parts.append(f"  - `{c.get('name', '')}`{bases}")

        if any(kw in msg for kw in ["function", "functions", "method", "def"]):
            fns = self._call("get_functions", tool_calls, repository_id=context.repository_id)
            fn_list = fns.get("functions", [])
            parts.append(f"**Functions:** {len(fn_list)} found")
            for f in fn_list[:10]:
                sig = f"({f.get('parameters', '')})"
                ret = f" -> {f.get('return_type')}" if f.get("return_type") else ""
                parts.append(f"  - `{f.get('name', '')}{sig}{ret}`")

        if any(kw in msg for kw in ["import", "imports", "depend"]):
            imps = self._call("get_imports", tool_calls, repository_id=context.repository_id)
            imp_list = imps.get("imports", [])
            parts.append(f"**Imports:** {len(imp_list)} found")
            for i in imp_list[:10]:
                parts.append(f"  - `{i.get('module', '')}.{i.get('name', '')}`")

        if not parts:
            search = self._call("search_code", tool_calls, repository_id=context.repository_id, query=context.user_message)
            results = search.get("results", [])
            parts.append(f"**Code search:** {len(results)} results")
            for r in results[:5]:
                parts.append(f"  - `{r.get('entity_name', '')}` in `{r.get('file_path', '')}`")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            tool_calls=tool_calls, duration_seconds=round(time.time() - start, 3),
        )

    def _call(self, tool: str, tool_calls: list, **kwargs) -> dict:
        if not self.tools:
            return {}
        result = self.tools.execute(tool, **kwargs)
        tool_calls.append({"tool": tool, "status": result.get("status")})
        return result.get("data", {}) if result.get("status") == "success" else {}

    def can_handle(self, message: str) -> float:
        score = super().can_handle(message)
        msg = message.lower()
        if any(kw in msg for kw in ["explain", "function", "class", "code", "method"]):
            score = max(score, 0.85)
        return score


# ------------------------------------------------------------------
# 3. Documentation Expert
# ------------------------------------------------------------------

class DocumentationExpert(BaseAgent):
    name = "documentation_expert"
    description = "Generates and retrieves documentation using the Documentation Engine."
    capabilities = ["documentation", "docs", "document", "readme", "generate docs", "onboarding", "changelog"]

    def __init__(self, db=None):
        super().__init__(db)
        self.tools = ToolExecutor(db) if db else None

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        parts = []
        tool_calls = []

        if not context.repository_id:
            return AgentResponse(agent_name=self.name, content="Please specify a repository.", status="error")

        msg = context.user_message.lower()
        if any(kw in msg for kw in ["generate", "create", "update", "rebuild"]):
            stats = self._call("generate_documentation", tool_calls, repository_id=context.repository_id)
            parts.append(f"**Documentation generated:**")
            parts.append(f"  - Created: {stats.get('documents_created', 0)}")
            parts.append(f"  - Updated: {stats.get('documents_updated', 0)}")
            parts.append(f"  - Skipped: {stats.get('documents_skipped', 0)}")
        else:
            docs = self._call("get_documentation", tool_calls, repository_id=context.repository_id)
            doc_list = docs.get("documents", [])
            parts.append(f"**Documentation:** {len(doc_list)} documents")
            for d in doc_list[:10]:
                parts.append(f"  - [{d.get('doc_type', '')}] **{d.get('title', '')}** — {(d.get('summary') or '')[:80]}")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            tool_calls=tool_calls, duration_seconds=round(time.time() - start, 3),
        )

    def _call(self, tool: str, tool_calls: list, **kwargs) -> dict:
        if not self.tools:
            return {}
        result = self.tools.execute(tool, **kwargs)
        tool_calls.append({"tool": tool, "status": result.get("status")})
        return result.get("data", {}) if result.get("status") == "success" else {}

    def can_handle(self, message: str) -> float:
        score = super().can_handle(message)
        msg = message.lower()
        if any(kw in msg for kw in ["document", "docs", "readme", "changelog"]):
            score = max(score, 0.85)
        return score


# ------------------------------------------------------------------
# 4. Architecture Expert
# ------------------------------------------------------------------

class ArchitectureExpert(BaseAgent):
    name = "architecture_expert"
    description = "Explains architecture, dependencies, and diagrams."
    capabilities = ["architecture", "layer", "module", "component", "dependency", "diagram", "violation", "structure"]

    def __init__(self, db=None):
        super().__init__(db)
        self.tools = ToolExecutor(db) if db else None

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        parts = []
        tool_calls = []

        if not context.repository_id:
            return AgentResponse(agent_name=self.name, content="Please specify a repository.", status="error")

        msg = context.user_message.lower()

        arch = self._call("get_architecture", tool_calls, repository_id=context.repository_id)
        models = arch.get("models", [])
        parts.append(f"**Architecture models:** {len(models)}")
        for m in models:
            parts.append(f"  - [{m.get('model_type', '')}] {m.get('name', '')}")

        if any(kw in msg for kw in ["depend", "import"]):
            deps = self._call("get_dependencies", tool_calls, repository_id=context.repository_id)
            mod_deps = deps.get("module_dependencies", {})
            parts.append(f"**Module dependencies:** {len(mod_deps)} modules")

        if any(kw in msg for kw in ["call", "callgraph"]):
            cg = self._call("get_callgraph", tool_calls, repository_id=context.repository_id)
            parts.append(f"**Call graph:** {cg.get('node_count', 0)} nodes, {cg.get('edge_count', 0)} edges")

        if any(kw in msg for kw in ["violation", "issue", "problem"]):
            vs = self._call("get_violations", tool_calls, repository_id=context.repository_id)
            v_list = vs.get("violations", [])
            parts.append(f"**Violations:** {len(v_list)} detected")
            for v in v_list[:5]:
                parts.append(f"  - [{v.get('severity', '')}] {v.get('description', '')[:80]}")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            tool_calls=tool_calls, duration_seconds=round(time.time() - start, 3),
        )

    def _call(self, tool: str, tool_calls: list, **kwargs) -> dict:
        if not self.tools:
            return {}
        result = self.tools.execute(tool, **kwargs)
        tool_calls.append({"tool": tool, "status": result.get("status")})
        return result.get("data", {}) if result.get("status") == "success" else {}

    def can_handle(self, message: str) -> float:
        score = super().can_handle(message)
        msg = message.lower()
        if any(kw in msg for kw in ["architecture", "layer", "diagram", "structure"]):
            score = max(score, 0.85)
        return score


# ------------------------------------------------------------------
# 5. Impact Expert
# ------------------------------------------------------------------

class ImpactExpert(BaseAgent):
    name = "impact_expert"
    description = "Answers 'What happens if I change X?' using the Impact Analysis Engine."
    capabilities = ["impact", "change", "risk", "affect", "what if", "break", "modify"]

    def __init__(self, db=None):
        super().__init__(db)
        self.tools = ToolExecutor(db) if db else None

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        parts = []
        tool_calls = []

        if not context.repository_id:
            return AgentResponse(agent_name=self.name, content="Please specify a repository.", status="error")

        msg = context.user_message.lower()

        if any(kw in msg for kw in ["analyze", "run", "check"]):
            stats = self._call("analyze_impact", tool_calls, repository_id=context.repository_id)
            parts.append(f"**Impact analysis:**")
            parts.append(f"  - Changes: {stats.get('total_changes', 0)}")
            parts.append(f"  - Affected: {stats.get('total_affected', 0)}")
            parts.append(f"  - Risk: {stats.get('overall_risk_level', 'low')} ({stats.get('overall_risk_score', 0):.2f})")
        elif context.selected_entities:
            for entity in context.selected_entities[:5]:
                impact = self._call("get_impact", tool_calls, repository_id=context.repository_id, entity_name=entity)
                if impact.get("error"):
                    parts.append(f"  - `{entity}`: no impact data")
                else:
                    parts.append(f"  - `{entity}`: risk={impact.get('risk_level', 'low')} deps={impact.get('direct_dependents', 0)}")
        else:
            risk = self._call("get_risk", tool_calls, repository_id=context.repository_id)
            if risk.get("error"):
                parts.append("No risk assessment available. Run impact analysis first.")
            else:
                parts.append(f"**Risk assessment:** {risk.get('risk_level', 'low')} ({risk.get('risk_score', 0):.2f})")
                parts.append(f"{risk.get('summary', '')}")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            tool_calls=tool_calls, duration_seconds=round(time.time() - start, 3),
        )

    def _call(self, tool: str, tool_calls: list, **kwargs) -> dict:
        if not self.tools:
            return {}
        result = self.tools.execute(tool, **kwargs)
        tool_calls.append({"tool": tool, "status": result.get("status")})
        return result.get("data", {}) if result.get("status") == "success" else {}

    def can_handle(self, message: str) -> float:
        score = super().can_handle(message)
        msg = message.lower()
        if any(kw in msg for kw in ["impact", "what if", "change", "risk", "affect"]):
            score = max(score, 0.9)
        return score


# ------------------------------------------------------------------
# 6. Search Expert
# ------------------------------------------------------------------

class SearchExpert(BaseAgent):
    name = "search_expert"
    description = "Semantic code search using Vector Search."
    capabilities = ["search", "find", "look for", "where", "locate", "query"]

    def __init__(self, db=None):
        super().__init__(db)
        self.tools = ToolExecutor(db) if db else None

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        parts = []
        tool_calls = []

        if not context.repository_id:
            return AgentResponse(agent_name=self.name, content="Please specify a repository.", status="error")

        result = self._call("search_code", tool_calls, repository_id=context.repository_id, query=context.user_message)
        results = result.get("results", [])
        parts.append(f"**Search results:** {len(results)} matches for \"{context.user_message[:50]}\"")
        for r in results[:10]:
            parts.append(f"  - `{r.get('entity_name', '')}` in `{r.get('file_path', '')}` (score: {r.get('score', 0):.3f})")

        if not results:
            parts.append("No results found. Try a different query.")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            tool_calls=tool_calls, duration_seconds=round(time.time() - start, 3),
        )

    def _call(self, tool: str, tool_calls: list, **kwargs) -> dict:
        if not self.tools:
            return {}
        result = self.tools.execute(tool, **kwargs)
        tool_calls.append({"tool": tool, "status": result.get("status")})
        return result.get("data", {}) if result.get("status") == "success" else {}

    def can_handle(self, message: str) -> float:
        score = super().can_handle(message)
        msg = message.lower()
        if any(kw in msg for kw in ["search", "find", "look for", "where is", "locate"]):
            score = max(score, 0.9)
        return score


# ------------------------------------------------------------------
# 7. Workflow Planner
# ------------------------------------------------------------------

class WorkflowPlanner(BaseAgent):
    name = "workflow_planner"
    description = "Breaks complex requests into subtasks and routes to appropriate agents."
    capabilities = ["plan", "workflow", "steps", "help", "how to", "guide"]

    def __init__(self, db=None, agents: dict[str, BaseAgent] | None = None):
        super().__init__(db)
        self._agents = agents or {}

    def handle(self, context: AgentContext) -> AgentResponse:
        start = time.time()
        plan = self._create_plan(context)
        parts = [f"**Execution Plan** ({len(plan)} steps):\n"]
        for i, step in enumerate(plan, 1):
            parts.append(f"{i}. **{step['agent']}** — {step['task']}")

        return AgentResponse(
            agent_name=self.name, content="\n".join(parts),
            data={"plan": plan}, duration_seconds=round(time.time() - start, 3),
        )

    def _create_plan(self, context: AgentContext) -> list[dict]:
        msg = context.user_message.lower()
        plan = []

        if any(kw in msg for kw in ["overview", "summary", "describe"]):
            plan.append({"agent": "repository_expert", "task": "Get repository overview"})
            plan.append({"agent": "architecture_expert", "task": "Analyze architecture"})
            plan.append({"agent": "documentation_expert", "task": "List documentation"})

        elif any(kw in msg for kw in ["impact", "change", "what if"]):
            plan.append({"agent": "impact_expert", "task": "Run impact analysis"})
            plan.append({"agent": "architecture_expert", "task": "Check for violations"})

        elif any(kw in msg for kw in ["document", "docs"]):
            plan.append({"agent": "documentation_expert", "task": "Generate documentation"})
            plan.append({"agent": "repository_expert", "task": "Verify repository context"})

        elif any(kw in msg for kw in ["search", "find"]):
            plan.append({"agent": "search_expert", "task": "Semantic code search"})
            plan.append({"agent": "code_expert", "task": "Explain matching entities"})

        else:
            # Default: gather broad context
            plan.append({"agent": "repository_expert", "task": "Get repository info"})
            plan.append({"agent": "code_expert", "task": "Explain code entities"})

        return plan

    def can_handle(self, message: str) -> float:
        msg = message.lower()
        if any(kw in msg for kw in ["plan", "workflow", "steps", "how to"]):
            return 0.9
        # Complex multi-part requests
        if len(message.split()) > 15:
            return 0.5
        return 0.1
