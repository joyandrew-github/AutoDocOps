"""GraphQueryService — provides read-only graph analytics."""
from app.db.neo4j import Neo4jClient
from app.engines.graph_engine.cypher_builder import (
    AnalyticsBuilder,
    NodeBuilder,
    RelationshipBuilder,
    CypherQuery,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

ANALYTICS = AnalyticsBuilder


class GraphQueryService:
    """Read-only queries against the Neo4j knowledge graph."""

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client

    def get_statistics(self, repository_id: int) -> dict:
        """Get node/relationship counts for a repository."""
        repo_uid = f"repo:{repository_id}"

        # Node counts by label
        cq = ANALYTICS.graph_statistics(repo_uid)
        label_counts = {}
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    label_counts[record["label"]] = record["count"]
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")

        # Total relationships
        rel_count = 0
        try:
            cq_rels = CypherQuery(
                query=(
                    "MATCH (r:Repository {uid: $repo_uid})-[:CONTAINS*]->(n) "
                    "OPTIONAL MATCH (n)-[rel]->() "
                    "RETURN count(rel) AS count"
                ),
                params={"repo_uid": repo_uid},
            )
            with self.neo4j.get_session() as session:
                result = session.run(cq_rels.query, **cq_rels.params)
                record = result.single()
                if record:
                    rel_count = record["count"]
        except Exception as e:
            logger.error(f"Failed to count relationships: {e}")

        return {
            "repository_id": repository_id,
            "total_nodes": sum(label_counts.values()),
            "total_relationships": rel_count,
            "node_counts": label_counts,
        }

    def get_node(self, element_id: str) -> dict | None:
        """Get a node by its element ID."""
        cq = NodeBuilder.get_node_by_element_id(element_id)
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                record = result.single()
                if record:
                    node = record["n"]
                    return {
                        "element_id": element_id,
                        "labels": record["labels"],
                        "properties": dict(node),
                    }
        except Exception as e:
            logger.error(f"Failed to get node {element_id}: {e}")
        return None

    def get_neighbors(self, element_id: str, direction: str = "both", limit: int = 50) -> list[dict]:
        """Get neighbors of a node."""
        cq = RelationshipBuilder.get_neighbors(element_id, direction, limit)
        neighbors = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    neighbors.append({
                        "element_id": record["eid"],
                        "labels": record["labels"],
                        "relationship_type": record["rel_type"],
                        "properties": dict(record["m"]),
                    })
        except Exception as e:
            logger.error(f"Failed to get neighbors for {element_id}: {e}")
        return neighbors

    def most_connected_files(self, repository_id: int, limit: int = 10) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.most_connected_files(repo_uid, limit)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "path": record["path"],
                        "language": record["language"],
                        "connections": record["connections"],
                    })
        except Exception as e:
            logger.error(f"Failed to get most connected files: {e}")
        return results

    def largest_classes(self, repository_id: int, limit: int = 10) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.largest_classes(repo_uid, limit)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "name": record["name"],
                        "file_path": record["file_path"],
                        "method_count": record["method_count"],
                    })
        except Exception as e:
            logger.error(f"Failed to get largest classes: {e}")
        return results

    def dependency_graph(self, repository_id: int) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.dependency_graph(repo_uid)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "file_path": record["file_path"],
                        "dependency": record["dependency"],
                        "version": record["version"],
                    })
        except Exception as e:
            logger.error(f"Failed to get dependency graph: {e}")
        return results

    def import_graph(self, repository_id: int) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.import_graph(repo_uid)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "file_path": record["file_path"],
                        "module": record["module"],
                        "name": record["name"],
                    })
        except Exception as e:
            logger.error(f"Failed to get import graph: {e}")
        return results

    def call_graph(self, repository_id: int) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.call_graph(repo_uid)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "caller": record["caller"],
                        "caller_type": record["caller_type"],
                        "callee": record["callee"],
                        "callee_type": record["callee_type"],
                    })
        except Exception as e:
            logger.error(f"Failed to get call graph: {e}")
        return results

    def language_statistics(self, repository_id: int) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.language_statistics(repo_uid)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "language": record["language"],
                        "file_count": record["file_count"],
                    })
        except Exception as e:
            logger.error(f"Failed to get language statistics: {e}")
        return results

    def framework_statistics(self, repository_id: int) -> list[dict]:
        repo_uid = f"repo:{repository_id}"
        cq = ANALYTICS.framework_statistics(repo_uid)
        results = []
        try:
            with self.neo4j.get_session() as session:
                result = session.run(cq.query, **cq.params)
                for record in result:
                    results.append({
                        "name": record["name"],
                        "version": record["version"],
                        "confidence": record["confidence"],
                    })
        except Exception as e:
            logger.error(f"Failed to get framework statistics: {e}")
        return results
