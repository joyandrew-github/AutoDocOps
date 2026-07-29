from neo4j import GraphDatabase
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Neo4jClient:
    """Neo4j database client."""
    
    def __init__(self) -> None:
        self.driver: Optional[GraphDatabase.driver] = None
    
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Verify connection
            self.driver.verify_connectivity()
            logger.info("Neo4j connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def get_session(self):
        """Get a Neo4j session."""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self.driver.session()


# Global Neo4j client instance
neo4j_client = Neo4jClient()


def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    return neo4j_client


def init_neo4j() -> None:
    """Initialize Neo4j connection."""
    neo4j_client.connect()
