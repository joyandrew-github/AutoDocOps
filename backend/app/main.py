from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db
from app.db.neo4j import init_neo4j
from app.db.redis import init_redis
from app.api.v1.api import api_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        init_db()
        logger.info("PostgreSQL initialized")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
    
    try:
        init_neo4j()
        logger.info("Neo4j initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")
    
    try:
        init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    from app.db.neo4j import neo4j_client
    from app.db.redis import redis_client
    neo4j_client.close()
    redis_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade AI platform for automated documentation operations",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "v1_prefix": settings.API_V1_PREFIX,
    }
