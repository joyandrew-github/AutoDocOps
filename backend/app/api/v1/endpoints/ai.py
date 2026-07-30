"""API endpoints for the AI Multi-Agent System."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.ai_engine.orchestrator import AgentOrchestrator
from app.engines.ai_engine.base import AgentContext
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIPlanRequest,
    AIPlanResponse,
    AIPlanStep,
    AIExecuteRequest,
    AIExecuteResponse,
    AIExecuteStepResult,
    AIHistoryMessage,
    AIAgentInfo,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_orchestrator(db: Session = Depends(get_db)) -> AgentOrchestrator:
    return AgentOrchestrator(db)


@router.post(
    "/ai/chat",
    response_model=AIChatResponse,
    summary="AI Chat",
    description="Send a message to the AI system. Auto-routes to the best agent.",
)
def ai_chat(
    request: AIChatRequest,
    orchestrator: AgentOrchestrator = Depends(_get_orchestrator),
):
    ctx = AgentContext(
        repository_id=request.repository_id,
        conversation_id=request.conversation_id,
        user_message=request.message,
        selected_entities=request.selected_entities,
    )
    try:
        resp = orchestrator.chat(ctx)
        return AIChatResponse(
            agent_name=resp.agent_name,
            content=resp.content,
            conversation_id=ctx.conversation_id,
            tool_calls=resp.tool_calls,
            status=resp.status,
            duration_seconds=resp.duration_seconds,
            error=resp.error,
        )
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during AI processing.",
        )


@router.post(
    "/ai/plan",
    response_model=AIPlanResponse,
    summary="Create execution plan",
    description="Create a multi-step execution plan for a request.",
)
def ai_plan(
    request: AIPlanRequest,
    orchestrator: AgentOrchestrator = Depends(_get_orchestrator),
):
    ctx = AgentContext(
        repository_id=request.repository_id,
        user_message=request.message,
    )
    plan = orchestrator.plan(ctx)
    return AIPlanResponse(plan=[AIPlanStep(**s) for s in plan])


@router.post(
    "/ai/execute",
    response_model=AIExecuteResponse,
    summary="Execute plan",
    description="Execute a plan (sequential or parallel). If no plan provided, auto-generates one.",
)
def ai_execute(
    request: AIExecuteRequest,
    orchestrator: AgentOrchestrator = Depends(_get_orchestrator),
):
    ctx = AgentContext(
        repository_id=request.repository_id,
        conversation_id=request.conversation_id,
        user_message=request.message,
        selected_entities=request.selected_entities,
    )
    plan = [{"agent": s.agent, "task": s.task} for s in request.plan] if request.plan else None
    try:
        responses = orchestrator.execute(ctx, plan=plan, parallel=request.parallel)
        return AIExecuteResponse(
            conversation_id=ctx.conversation_id,
            results=[
                AIExecuteStepResult(
                    agent_name=r.agent_name, content=r.content,
                    status=r.status, duration_seconds=r.duration_seconds, error=r.error,
                )
                for r in responses
            ],
        )
    except Exception as e:
        logger.error(f"AI execute failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during AI execution.",
        )


@router.get(
    "/ai/history",
    response_model=list[AIHistoryMessage],
    summary="Get conversation history",
    description="Get conversation history by conversation ID.",
)
def ai_history(
    conversation_id: str,
    limit: int = 50,
    orchestrator: AgentOrchestrator = Depends(_get_orchestrator),
):
    history = orchestrator.get_history(conversation_id, limit)
    return [
        AIHistoryMessage(
            role=m.get("role", ""), content=m.get("content", ""),
            agent=m.get("agent"), timestamp=m.get("timestamp"),
        )
        for m in history
    ]


@router.get(
    "/ai/agents",
    response_model=list[AIAgentInfo],
    summary="List agents",
    description="List all available AI agents and their capabilities.",
)
def ai_agents(
    orchestrator: AgentOrchestrator = Depends(_get_orchestrator),
):
    agents = orchestrator.list_agents()
    return [AIAgentInfo(**a) for a in agents]


@router.post(
    "/ai/stream",
    summary="Stream AI response",
    description="Stream an incremental AI response.",
)
def ai_stream(
    request: AIChatRequest,
    orchestrator: AgentOrchestrator = Depends(_get_orchestrator),
):
    ctx = AgentContext(
        repository_id=request.repository_id,
        conversation_id=request.conversation_id,
        user_message=request.message,
        selected_entities=request.selected_entities,
    )
    return StreamingResponse(
        orchestrator.stream(ctx),
        media_type="text/plain",
    )
