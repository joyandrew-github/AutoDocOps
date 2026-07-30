"""Comprehensive tests for the AI Multi-Agent System."""
import pytest
from unittest.mock import MagicMock, patch
from app.engines.ai_engine.base import (
    AgentContext, AgentResponse, BaseAgent, ConversationMemory,
)
from app.engines.ai_engine.tools import ToolExecutor
from app.engines.ai_engine.agents import (
    RepositoryExpert, CodeExpert, DocumentationExpert,
    ArchitectureExpert, ImpactExpert, SearchExpert, WorkflowPlanner,
)
from app.engines.ai_engine.orchestrator import AgentRegistry, AgentOrchestrator


# ==================================================================
# AgentContext
# ==================================================================

class TestAgentContext:

    def test_defaults(self):
        ctx = AgentContext()
        assert ctx.repository_id is None
        assert ctx.user_message == ""
        assert ctx.selected_entities == []

    def test_clone(self):
        ctx = AgentContext(repository_id=1, user_message="hello")
        c2 = ctx.clone(user_message="world")
        assert c2.user_message == "world"
        assert c2.repository_id == 1
        assert ctx.user_message == "hello"

    def test_clone_entities(self):
        ctx = AgentContext(selected_entities=["a"])
        c2 = ctx.clone()
        c2.selected_entities.append("b")
        assert "b" not in ctx.selected_entities

    def test_metadata(self):
        ctx = AgentContext(metadata={"key": "val"})
        c2 = ctx.clone(metadata={"extra": True})
        assert c2.metadata["key"] == "val"
        assert c2.metadata["extra"] is True


# ==================================================================
# ConversationMemory
# ==================================================================

class TestConversationMemory:

    def test_get_or_create(self):
        mem = ConversationMemory()
        cid = mem.get_or_create()
        assert cid is not None
        cid2 = mem.get_or_create(cid)
        assert cid2 == cid

    def test_add_messages(self):
        mem = ConversationMemory()
        cid = mem.get_or_create("test-conv")
        mem.add_user_message(cid, "hello")
        mem.add_agent_message(cid, "bot", "hi")
        history = mem.get_history(cid)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "agent"

    def test_history_limit(self):
        mem = ConversationMemory()
        cid = mem.get_or_create("test")
        for i in range(10):
            mem.add_user_message(cid, f"msg {i}")
        assert len(mem.get_history(cid, limit=3)) == 3

    def test_context_summary(self):
        mem = ConversationMemory()
        cid = mem.get_or_create("test")
        mem.add_user_message(cid, "hello world")
        summary = mem.get_context_summary(cid)
        assert "hello world" in summary

    def test_context_summary_empty(self):
        mem = ConversationMemory()
        assert mem.get_context_summary("nonexistent") == ""

    def test_clear(self):
        mem = ConversationMemory()
        cid = mem.get_or_create("test")
        mem.add_user_message(cid, "msg")
        mem.clear(cid)
        assert mem.get_history(cid) == []

    def test_list_conversations(self):
        mem = ConversationMemory()
        mem.get_or_create("a")
        mem.get_or_create("b")
        assert "a" in mem.list_conversations()
        assert "b" in mem.list_conversations()


# ==================================================================
# BaseAgent
# ==================================================================

class TestBaseAgent:

    def test_handle_raises(self):
        agent = BaseAgent()
        with pytest.raises(NotImplementedError):
            agent.handle(AgentContext())

    def test_stream_default(self):
        class DummyAgent(BaseAgent):
            name = "dummy"
            def handle(self, ctx):
                return AgentResponse(content="ok")
        agent = DummyAgent()
        chunks = list(agent.stream(AgentContext()))
        assert chunks == ["ok"]

    def test_can_handle(self):
        class DummyAgent(BaseAgent):
            capabilities = ["search"]
        agent = DummyAgent()
        assert agent.can_handle("search for X") >= 0.6
        assert agent.can_handle("unrelated query") == 0.0

    def test_repr(self):
        agent = BaseAgent()
        assert "BaseAgent" in repr(agent)


# ==================================================================
# ToolExecutor
# ==================================================================

class TestToolExecutor:

    @pytest.fixture
    def executor(self):
        db = MagicMock()
        return ToolExecutor(db)

    def test_available_tools(self, executor):
        tools = executor.available_tools
        assert "search_code" in tools
        assert "get_repository" in tools
        assert "analyze_impact" in tools
        assert len(tools) >= 17

    def test_unknown_tool(self, executor):
        result = executor.execute("nonexistent_tool")
        assert result["status"] == "error"

    def test_execute_success(self, executor):
        executor._registry["test_tool"] = lambda **kw: {"ok": True}
        result = executor.execute("test_tool")
        assert result["status"] == "success"
        assert result["data"]["ok"] is True

    def test_execute_failure(self, executor):
        executor._registry["bad_tool"] = lambda **kw: (_ for _ in ()).throw(ValueError("fail"))
        result = executor.execute("bad_tool")
        assert result["status"] == "error"


# ==================================================================
# Individual Agents
# ==================================================================

class TestRepositoryExpert:

    def test_no_repo(self):
        agent = RepositoryExpert()
        resp = agent.handle(AgentContext(user_message="overview"))
        assert resp.status == "error"

    def test_handle(self):
        agent = RepositoryExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"name": "MyRepo", "files": []}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="overview"))
        assert "MyRepo" in resp.content

    def test_can_handle(self):
        agent = RepositoryExpert()
        assert agent.can_handle("tell me about the repository") >= 0.8
        assert agent.can_handle("xyz") == 0.0


class TestCodeExpert:

    def test_no_repo(self):
        agent = CodeExpert()
        resp = agent.handle(AgentContext(user_message="classes"))
        assert resp.status == "error"

    def test_classes(self):
        agent = CodeExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"classes": [{"name": "Foo", "bases": "", "docstring": ""}]}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="list classes"))
        assert "Foo" in resp.content

    def test_can_handle(self):
        agent = CodeExpert()
        assert agent.can_handle("explain the function") >= 0.85


class TestDocumentationExpert:

    def test_no_repo(self):
        agent = DocumentationExpert()
        resp = agent.handle(AgentContext(user_message="docs"))
        assert resp.status == "error"

    def test_list_docs(self):
        agent = DocumentationExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"documents": [{"id": 1, "title": "README", "doc_type": "readme", "summary": "ok"}]}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="list docs"))
        assert "README" in resp.content

    def test_generate(self):
        agent = DocumentationExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"documents_created": 2, "documents_updated": 1, "documents_skipped": 0}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="generate documentation"))
        assert "Created: 2" in resp.content

    def test_can_handle(self):
        agent = DocumentationExpert()
        assert agent.can_handle("show me the documentation") >= 0.85


class TestArchitectureExpert:

    def test_no_repo(self):
        agent = ArchitectureExpert()
        resp = agent.handle(AgentContext(user_message="architecture"))
        assert resp.status == "error"

    def test_handle(self):
        agent = ArchitectureExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"models": [{"id": 1, "model_type": "layers", "name": "Layers"}]}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="show architecture"))
        assert "Layers" in resp.content

    def test_can_handle(self):
        agent = ArchitectureExpert()
        assert agent.can_handle("explain the architecture") >= 0.85


class TestImpactExpert:

    def test_no_repo(self):
        agent = ImpactExpert()
        resp = agent.handle(AgentContext(user_message="impact"))
        assert resp.status == "error"

    def test_analyze(self):
        agent = ImpactExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"total_changes": 3, "total_affected": 5, "overall_risk_level": "medium", "overall_risk_score": 0.4}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="analyze impact"))
        assert "medium" in resp.content

    def test_risk(self):
        agent = ImpactExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"risk_level": "low", "risk_score": 0.1, "summary": "ok"}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="what is the risk"))
        assert "low" in resp.content

    def test_can_handle(self):
        agent = ImpactExpert()
        assert agent.can_handle("what is the impact of changing X") >= 0.9


class TestSearchExpert:

    def test_no_repo(self):
        agent = SearchExpert()
        resp = agent.handle(AgentContext(user_message="search"))
        assert resp.status == "error"

    def test_search(self):
        agent = SearchExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"results": [{"entity_name": "process", "file_path": "main.py", "score": 0.9}]}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="search for process"))
        assert "process" in resp.content

    def test_no_results(self):
        agent = SearchExpert()
        agent.tools = MagicMock()
        agent.tools.execute.return_value = {"status": "success", "data": {"results": []}}
        resp = agent.handle(AgentContext(repository_id=1, user_message="search for xyz"))
        assert "No results" in resp.content

    def test_can_handle(self):
        agent = SearchExpert()
        assert agent.can_handle("find the authentication handler") >= 0.9


class TestWorkflowPlanner:

    def test_overview_plan(self):
        planner = WorkflowPlanner()
        resp = planner.handle(AgentContext(user_message="give me an overview"))
        assert len(resp.data["plan"]) >= 2

    def test_impact_plan(self):
        planner = WorkflowPlanner()
        resp = planner.handle(AgentContext(user_message="what is the impact of changes"))
        assert any(s["agent"] == "impact_expert" for s in resp.data["plan"])

    def test_docs_plan(self):
        planner = WorkflowPlanner()
        resp = planner.handle(AgentContext(user_message="generate documentation"))
        assert any(s["agent"] == "documentation_expert" for s in resp.data["plan"])

    def test_search_plan(self):
        planner = WorkflowPlanner()
        resp = planner.handle(AgentContext(user_message="search for process"))
        assert any(s["agent"] == "search_expert" for s in resp.data["plan"])

    def test_default_plan(self):
        planner = WorkflowPlanner()
        resp = planner.handle(AgentContext(user_message="hello"))
        assert len(resp.data["plan"]) >= 1

    def test_can_handle(self):
        planner = WorkflowPlanner()
        assert planner.can_handle("plan a workflow") >= 0.9
        assert planner.can_handle("x") <= 0.2


# ==================================================================
# AgentRegistry
# ==================================================================

class TestAgentRegistry:

    def test_register_and_get(self):
        reg = AgentRegistry()
        agent = RepositoryExpert()
        reg.register(agent)
        assert reg.get("repository_expert") is agent

    def test_get_unknown(self):
        reg = AgentRegistry()
        assert reg.get("unknown") is None

    def test_list_agents(self):
        reg = AgentRegistry()
        reg.register(RepositoryExpert())
        reg.register(CodeExpert())
        agents = reg.list_agents()
        assert len(agents) == 2
        names = [a["name"] for a in agents]
        assert "repository_expert" in names

    def test_route(self):
        reg = AgentRegistry()
        reg.register(RepositoryExpert())
        reg.register(SearchExpert())
        agent = reg.route("search for process")
        assert agent.name == "search_expert"

    def test_route_no_match(self):
        reg = AgentRegistry()
        agent = reg.route("xyzzy")
        assert agent is None

    def test_agents_property(self):
        reg = AgentRegistry()
        reg.register(CodeExpert())
        assert "code_expert" in reg.agents


# ==================================================================
# AgentOrchestrator
# ==================================================================

class TestAgentOrchestrator:

    @pytest.fixture
    def orchestrator(self):
        db = MagicMock()
        with patch.object(ToolExecutor, '__init__', lambda self, db: setattr(self, 'db', db) or setattr(self, '_registry', {})):
            orch = AgentOrchestrator(db)
        return orch

    def test_list_agents(self, orchestrator):
        agents = orchestrator.list_agents()
        names = [a["name"] for a in agents]
        assert "repository_expert" in names
        assert "code_expert" in names
        assert "documentation_expert" in names
        assert "architecture_expert" in names
        assert "impact_expert" in names
        assert "search_expert" in names
        assert "workflow_planner" in names
        assert len(names) == 7

    def test_chat_routing(self, orchestrator):
        # Mock all agent handles
        for agent in orchestrator.registry.agents.values():
            agent.tools = None
        ctx = AgentContext(repository_id=1, user_message="search for authentication")
        resp = orchestrator.chat(ctx)
        assert resp.agent_name in ["search_expert", "repository_expert"]

    def test_chat_no_route(self, orchestrator):
        # Remove all agents so nothing matches
        orchestrator.registry._agents = {}
        ctx = AgentContext(user_message="xyzzy")
        resp = orchestrator.chat(ctx)
        assert resp.status == "no_route"

    def test_chat_conversation_tracking(self, orchestrator):
        for agent in orchestrator.registry.agents.values():
            agent.tools = None
        ctx = AgentContext(repository_id=1, user_message="show repository info")
        resp = orchestrator.chat(ctx)
        history = orchestrator.get_history(ctx.conversation_id)
        assert len(history) >= 2  # user + agent

    def test_plan(self, orchestrator):
        ctx = AgentContext(user_message="give me an overview of the project")
        plan = orchestrator.plan(ctx)
        assert len(plan) >= 1

    def test_execute_sequential(self, orchestrator):
        for agent in orchestrator.registry.agents.values():
            agent.tools = None
        plan = [{"agent": "repository_expert", "task": "Get repo info"}]
        ctx = AgentContext(repository_id=1, user_message="info")
        responses = orchestrator.execute(ctx, plan=plan)
        assert len(responses) == 1

    def test_execute_parallel(self, orchestrator):
        for agent in orchestrator.registry.agents.values():
            agent.tools = None
        plan = [
            {"agent": "repository_expert", "task": "Get repo info"},
            {"agent": "code_expert", "task": "List code"},
        ]
        ctx = AgentContext(repository_id=1, user_message="info")
        responses = orchestrator.execute(ctx, plan=plan, parallel=True)
        assert len(responses) == 2

    def test_execute_unknown_agent(self, orchestrator):
        plan = [{"agent": "nonexistent_agent", "task": "Do something"}]
        ctx = AgentContext(user_message="test")
        responses = orchestrator.execute(ctx, plan=plan)
        assert responses[0].status == "error"

    def test_execute_auto_plan(self, orchestrator):
        for agent in orchestrator.registry.agents.values():
            agent.tools = None
        ctx = AgentContext(repository_id=1, user_message="overview")
        responses = orchestrator.execute(ctx)
        assert len(responses) >= 1

    def test_stream(self, orchestrator):
        for agent in orchestrator.registry.agents.values():
            agent.tools = None
        ctx = AgentContext(repository_id=1, user_message="show repository info")
        chunks = list(orchestrator.stream(ctx))
        assert len(chunks) >= 1

    def test_stream_no_route(self, orchestrator):
        orchestrator.registry._agents = {}
        ctx = AgentContext(user_message="xyzzy")
        chunks = list(orchestrator.stream(ctx))
        assert "not sure" in chunks[0].lower()

    def test_get_history_empty(self, orchestrator):
        assert orchestrator.get_history("nonexistent") == []
