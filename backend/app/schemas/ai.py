"""Pydantic schemas for the AI Multi-Agent System."""
from typing import Any
from pydantic import BaseModel


class AIChatRequest(BaseModel):
    message: str
    repository_id: int | None = None
    conversation_id: str | None = None
    selected_entities: list[str] = []


class AIChatResponse(BaseModel):
    agent_name: str
    content: str
    conversation_id: str | None = None
    tool_calls: list[dict] = []
    status: str = "success"
    duration_seconds: float = 0.0
    error: str | None = None


class AIPlanRequest(BaseModel):
    message: str
    repository_id: int | None = None


class AIPlanStep(BaseModel):
    agent: str
    task: str


class AIPlanResponse(BaseModel):
    plan: list[AIPlanStep] = []


class AIExecuteRequest(BaseModel):
    message: str
    repository_id: int | None = None
    conversation_id: str | None = None
    selected_entities: list[str] = []
    plan: list[AIPlanStep] | None = None
    parallel: bool = False


class AIExecuteStepResult(BaseModel):
    agent_name: str
    content: str
    status: str = "success"
    duration_seconds: float = 0.0
    error: str | None = None


class AIExecuteResponse(BaseModel):
    conversation_id: str | None = None
    results: list[AIExecuteStepResult] = []


class AIHistoryMessage(BaseModel):
    role: str
    content: str
    agent: str | None = None
    timestamp: float | None = None


class AIAgentInfo(BaseModel):
    name: str
    description: str
    capabilities: list[str] = []
