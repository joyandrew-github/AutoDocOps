"""AgentOrchestrator — routes, plans, and executes agent workflows."""
from __future__ import annotations
import time
import concurrent.futures
from typing import Generator
from sqlalchemy.orm import Session
from app.engines.ai_engine.base import BaseAgent, AgentContext, AgentResponse, ConversationMemory
from app.engines.ai_engine.agents import (
    RepositoryExpert,
    CodeExpert,
    DocumentationExpert,
    ArchitectureExpert,
    ImpactExpert,
    SearchExpert,
    WorkflowPlanner,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentRegistry:
    """Registry of available agents."""

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def list_agents(self) -> list[dict]:
        return [
            {"name": a.name, "description": a.description, "capabilities": a.capabilities}
            for a in self._agents.values()
        ]

    def route(self, message: str) -> BaseAgent | None:
        best_agent: BaseAgent | None = None
        best_score = 0.0
        for agent in self._agents.values():
            score = agent.can_handle(message)
            if score > best_score:
                best_score = score
                best_agent = agent
        return best_agent if best_score > 0.1 else None

    @property
    def agents(self) -> dict[str, BaseAgent]:
        return dict(self._agents)


class AgentOrchestrator:
    """Orchestrates agent execution with routing, planning, parallel execution, and streaming."""

    def __init__(self, db: Session):
        self.db = db
        self.registry = AgentRegistry()
        self.memory = ConversationMemory()
        self._register_agents()

    def _register_agents(self) -> None:
        agents = [
            RepositoryExpert(self.db),
            CodeExpert(self.db),
            DocumentationExpert(self.db),
            ArchitectureExpert(self.db),
            ImpactExpert(self.db),
            SearchExpert(self.db),
        ]
        for a in agents:
            self.registry.register(a)
        planner = WorkflowPlanner(self.db, agents=self.registry.agents)
        self.registry.register(planner)

    # ------------------------------------------------------------------
    # Chat — single-agent auto-routed execution
    # ------------------------------------------------------------------

    def chat(self, context: AgentContext) -> AgentResponse:
        cid = self.memory.get_or_create(context.conversation_id)
        context.conversation_id = cid
        self.memory.add_user_message(cid, context.user_message)

        agent = self.registry.route(context.user_message)
        if not agent:
            resp = AgentResponse(agent_name="system", content="I'm not sure how to help with that. Try asking about code, architecture, impact, or documentation.", status="no_route")
            self.memory.add_agent_message(cid, "system", resp.content)
            return resp

        logger.info(f"Routing to {agent.name} (conversation={cid[:8]})")
        resp = agent.handle(context)
        self.memory.add_agent_message(cid, agent.name, resp.content)
        return resp

    # ------------------------------------------------------------------
    # Plan — create an execution plan
    # ------------------------------------------------------------------

    def plan(self, context: AgentContext) -> list[dict]:
        planner = self.registry.get("workflow_planner")
        if not planner:
            return [{"agent": "repository_expert", "task": context.user_message}]
        resp = planner.handle(context)
        return resp.data.get("plan", [])

    # ------------------------------------------------------------------
    # Execute — run a plan (supports sequential and parallel)
    # ------------------------------------------------------------------

    def execute(self, context: AgentContext, plan: list[dict] | None = None, parallel: bool = False) -> list[AgentResponse]:
        if plan is None:
            plan = self.plan(context)

        cid = self.memory.get_or_create(context.conversation_id)
        context.conversation_id = cid
        self.memory.add_user_message(cid, context.user_message)

        if parallel and len(plan) > 1:
            return self._execute_parallel(context, plan, cid)
        return self._execute_sequential(context, plan, cid)

    def _execute_sequential(self, context: AgentContext, plan: list[dict], cid: str) -> list[AgentResponse]:
        responses: list[AgentResponse] = []
        for step in plan:
            agent = self.registry.get(step["agent"])
            if not agent:
                responses.append(AgentResponse(agent_name=step["agent"], content=f"Agent not found: {step['agent']}", status="error"))
                continue
            step_ctx = context.clone(user_message=step.get("task", context.user_message))
            resp = agent.handle(step_ctx)
            self.memory.add_agent_message(cid, agent.name, resp.content)
            responses.append(resp)
        return responses

    def _execute_parallel(self, context: AgentContext, plan: list[dict], cid: str) -> list[AgentResponse]:
        responses: list[AgentResponse] = [None] * len(plan)

        def _run(idx: int, step: dict) -> tuple[int, AgentResponse]:
            agent = self.registry.get(step["agent"])
            if not agent:
                return idx, AgentResponse(agent_name=step["agent"], content=f"Agent not found", status="error")
            step_ctx = context.clone(user_message=step.get("task", context.user_message))
            return idx, agent.handle(step_ctx)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(_run, i, s) for i, s in enumerate(plan)]
            for future in concurrent.futures.as_completed(futures):
                idx, resp = future.result()
                responses[idx] = resp
                self.memory.add_agent_message(cid, resp.agent_name, resp.content)

        return responses

    # ------------------------------------------------------------------
    # Stream — incremental streaming response
    # ------------------------------------------------------------------

    def stream(self, context: AgentContext) -> Generator[str, None, None]:
        cid = self.memory.get_or_create(context.conversation_id)
        context.conversation_id = cid
        self.memory.add_user_message(cid, context.user_message)

        agent = self.registry.route(context.user_message)
        if not agent:
            yield "I'm not sure how to help with that."
            return

        logger.info(f"Streaming from {agent.name} (conversation={cid[:8]})")
        full_content = ""
        for chunk in agent.stream(context):
            full_content += chunk
            yield chunk
        self.memory.add_agent_message(cid, agent.name, full_content)

    # ------------------------------------------------------------------
    # History / agents
    # ------------------------------------------------------------------

    def get_history(self, conversation_id: str, limit: int = 50) -> list[dict]:
        return self.memory.get_history(conversation_id, limit)

    def list_agents(self) -> list[dict]:
        return self.registry.list_agents()
