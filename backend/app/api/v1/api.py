from fastapi import APIRouter
from app.api.v1.endpoints import health, repositories, parser

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(repositories.router, tags=["repositories"])
api_router.include_router(parser.router, tags=["parser"])
