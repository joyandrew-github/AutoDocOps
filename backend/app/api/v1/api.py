from fastapi import APIRouter
from app.api.v1.endpoints import health, repositories, parser, memory, graph

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(repositories.router, tags=["repositories"])
api_router.include_router(parser.router, tags=["parser"])
api_router.include_router(memory.router, tags=["memory"])
api_router.include_router(graph.router, tags=["graph"])
