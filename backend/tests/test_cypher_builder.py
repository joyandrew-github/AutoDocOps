"""Unit tests for Cypher query builders."""
import pytest
from app.engines.graph_engine.cypher_builder import (
    CypherQuery,
    NodeBuilder,
    RelationshipBuilder,
    AnalyticsBuilder,
)


class TestNodeBuilder:
    """Test NodeBuilder Cypher query generation."""

    def test_merge_node_basic(self):
        cq = NodeBuilder.merge_node("Repository", "uid", "repo:1")
        assert "MERGE" in cq.query
        assert "Repository" in cq.query
        assert cq.params["uid"] == "repo:1"

    def test_merge_node_with_properties(self):
        cq = NodeBuilder.merge_node("File", "uid", "file:1", {"name": "main.py", "language": "Python"})
        assert "SET" in cq.query
        assert "n.name" in cq.query
        assert "n.language" in cq.query
        assert cq.params["name"] == "main.py"
        assert cq.params["language"] == "Python"

    def test_batch_merge_nodes(self):
        records = [
            {"uid": "f:1", "name": "a.py"},
            {"uid": "f:2", "name": "b.py"},
        ]
        cq = NodeBuilder.batch_merge_nodes("File", "uid", records)
        assert "UNWIND" in cq.query
        assert "MERGE" in cq.query
        assert len(cq.params["records"]) == 2

    def test_delete_node(self):
        cq = NodeBuilder.delete_node("File", "uid", "file:1")
        assert "DETACH DELETE" in cq.query
        assert cq.params["uid"] == "file:1"

    def test_batch_delete_nodes(self):
        cq = NodeBuilder.batch_delete_nodes("File", "uid", ["f:1", "f:2"])
        assert "UNWIND" in cq.query
        assert "DETACH DELETE" in cq.query
        assert len(cq.params["keys"]) == 2

    def test_get_node(self):
        cq = NodeBuilder.get_node("File", "uid", "file:1")
        assert "MATCH" in cq.query
        assert "RETURN n" in cq.query

    def test_get_node_by_element_id(self):
        cq = NodeBuilder.get_node_by_element_id("4:abc:123")
        assert "elementId" in cq.query
        assert cq.params["element_id"] == "4:abc:123"

    def test_merge_node_returns_cypher_query(self):
        cq = NodeBuilder.merge_node("Test", "id", 1)
        assert isinstance(cq, CypherQuery)

    def test_merge_node_no_properties_no_set(self):
        cq = NodeBuilder.merge_node("Test", "id", 1)
        assert "SET" not in cq.query


class TestRelationshipBuilder:
    """Test RelationshipBuilder Cypher query generation."""

    def test_merge_relationship(self):
        cq = RelationshipBuilder.merge_relationship(
            "Repository", "uid", "repo:1",
            "File", "uid", "file:1",
            "CONTAINS"
        )
        assert "MATCH (a:Repository" in cq.query
        assert "MATCH (b:File" in cq.query
        assert "MERGE (a)-[r:CONTAINS" in cq.query

    def test_merge_relationship_with_properties(self):
        cq = RelationshipBuilder.merge_relationship(
            "File", "uid", "f1", "File", "uid", "f2",
            "IMPORTS", {"weight": 1}
        )
        assert "weight" in cq.query
        assert cq.params["weight"] == 1

    def test_batch_merge_relationships(self):
        records = [
            {"from_val": "r:1", "to_val": "f:1"},
            {"from_val": "r:1", "to_val": "f:2"},
        ]
        cq = RelationshipBuilder.batch_merge_relationships(
            "Repository", "uid", "File", "uid", "CONTAINS", records
        )
        assert "UNWIND" in cq.query
        assert len(cq.params["records"]) == 2

    def test_delete_relationships(self):
        cq = RelationshipBuilder.delete_relationships(
            "File", "uid", "file:1", "IMPORTS"
        )
        assert "DELETE r" in cq.query
        assert "IMPORTS" in cq.query

    def test_get_neighbors_both(self):
        cq = RelationshipBuilder.get_neighbors("4:abc:1", "both", 25)
        assert "(n)-[r]-(m)" in cq.query
        assert cq.params["limit"] == 25

    def test_get_neighbors_outgoing(self):
        cq = RelationshipBuilder.get_neighbors("4:abc:1", "outgoing")
        assert "(n)-[r]->(m)" in cq.query

    def test_get_neighbors_incoming(self):
        cq = RelationshipBuilder.get_neighbors("4:abc:1", "incoming")
        assert "(n)<-[r]-(m)" in cq.query


class TestAnalyticsBuilder:
    """Test AnalyticsBuilder Cypher query generation."""

    def test_graph_statistics(self):
        cq = AnalyticsBuilder.graph_statistics("repo:1")
        assert "Repository" in cq.query
        assert cq.params["repo_uid"] == "repo:1"

    def test_most_connected_files(self):
        cq = AnalyticsBuilder.most_connected_files("repo:1", 5)
        assert "ORDER BY connections DESC" in cq.query
        assert cq.params["limit"] == 5

    def test_largest_classes(self):
        cq = AnalyticsBuilder.largest_classes("repo:1", 10)
        assert "Class" in cq.query
        assert "Method" in cq.query
        assert "ORDER BY method_count DESC" in cq.query

    def test_dependency_graph(self):
        cq = AnalyticsBuilder.dependency_graph("repo:1")
        assert "DEPENDS_ON" in cq.query
        assert "Dependency" in cq.query

    def test_import_graph(self):
        cq = AnalyticsBuilder.import_graph("repo:1")
        assert "IMPORTS" in cq.query
        assert "Import" in cq.query

    def test_call_graph(self):
        cq = AnalyticsBuilder.call_graph("repo:1")
        assert "CALLS" in cq.query

    def test_language_statistics(self):
        cq = AnalyticsBuilder.language_statistics("repo:1")
        assert "language" in cq.query
        assert "file_count" in cq.query

    def test_framework_statistics(self):
        cq = AnalyticsBuilder.framework_statistics("repo:1")
        assert "Framework" in cq.query
        assert "USES" in cq.query

    def test_all_builders_return_cypher_query(self):
        """All analytics builders should return CypherQuery instances."""
        uid = "repo:1"
        assert isinstance(AnalyticsBuilder.graph_statistics(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.most_connected_files(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.largest_classes(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.dependency_graph(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.import_graph(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.call_graph(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.language_statistics(uid), CypherQuery)
        assert isinstance(AnalyticsBuilder.framework_statistics(uid), CypherQuery)
