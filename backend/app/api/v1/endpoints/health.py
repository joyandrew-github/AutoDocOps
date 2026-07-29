from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.neo4j import get_neo4j_client
from app.db.redis import get_redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    neo4j_client = Depends(get_neo4j_client),
    redis_client = Depends(get_redis_client)
):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "services": {
            "database": "unknown",
            "neo4j": "unknown",
            "redis": "unknown"
        }
    }
    
    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Neo4j
    try:
        session = neo4j_client.get_session()
        session.run("RETURN 1")
        session.close()
        health_status["services"]["neo4j"] = "healthy"
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        health_status["services"]["neo4j"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.get_client().ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive"}
