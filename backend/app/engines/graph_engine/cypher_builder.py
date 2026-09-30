"""Reusable Cypher query builders for Neo4j graph operations."""
from dataclasses import dataclass, field


@dataclass
class CypherQuery:
    """Represents a parameterized Cypher query."""
    query: str
    params: dict = field(default_factory=dict)


class NodeBuilder:
    """Builds Cypher queries for node operations."""

    @staticmethod
    def merge_node(label: str, key_field: str, key_value, properties: dict | None = None) -> CypherQuery:
        """Build a MERGE query to create or update a node."""
        props = properties or {}
        set_clauses = ", ".join(f"n.{k} = ${k}" for k in props)
        set_part = f" SET {set_clauses}" if set_clauses else ""
        query = f"MERGE (n:{label} {{{key_field}: ${key_field}}}){set_part} RETURN n"
        params = {key_field: key_value, **props}
        return CypherQuery(query=query, params=params)

    @staticmethod
    def batch_merge_nodes(label: str, key_field: str, records: list[dict]) -> CypherQuery:
        """Build a batch MERGE query for multiple nodes using UNWIND."""
        query = (
            f"UNWIND $records AS rec "
            f"MERGE (n:{label} {{{key_field}: rec.{key_field}}}) "
            f"SET n += rec "
            f"RETURN count(n) AS count"
        )
        return CypherQuery(query=query, params={"records": records})

    @staticmethod
    def delete_node(label: str, key_field: str, key_value) -> CypherQuery:
        """Build a DELETE query for a node and its relationships."""
        query = f"MATCH (n:{label} {{{key_field}: ${key_field}}}) DETACH DELETE n"
        return CypherQuery(query=query, params={key_field: key_value})

    @staticmethod
    def batch_delete_nodes(label: str, key_field: str, key_values: list) -> CypherQuery:
        """Build a batch DELETE query for multiple nodes."""
        query = (
            f"UNWIND $keys AS key "
            f"MATCH (n:{label} {{{key_field}: key}}) "
            f"DETACH DELETE n"
        )
        return CypherQuery(query=query, params={"keys": key_values})

    @staticmethod
    def get_node(label: str, key_field: str, key_value) -> CypherQuery:
        """Build a query to get a single node."""
        query = f"MATCH (n:{label} {{{key_field}: ${key_field}}}) RETURN n"
        return CypherQuery(query=query, params={key_field: key_value})

    @staticmethod
    def get_node_by_id(node_id: int) -> CypherQuery:
        """Build a query to get a node by internal ID."""
        query = "MATCH (n) WHERE elementId(n) = $node_id RETURN n, labels(n) AS labels"
        return CypherQuery(query=query, params={"node_id": str(node_id)})

    @staticmethod
    def get_node_by_element_id(element_id: str) -> CypherQuery:
        """Build a query to get a node by element ID."""
        query = "MATCH (n) WHERE elementId(n) = $element_id RETURN n, labels(n) AS labels"
        return CypherQuery(query=query, params={"element_id": element_id})


class RelationshipBuilder:
    """Builds Cypher queries for relationship operations."""

    @staticmethod
    def merge_relationship(
        from_label: str, from_key: str, from_value,
        to_label: str, to_key: str, to_value,
        rel_type: str, properties: dict | None = None
    ) -> CypherQuery:
        """Build a MERGE query for a relationship."""
        props = properties or {}
        prop_str = ""
        if props:
            prop_parts = ", ".join(f"{k}: ${k}" for k in props)
            prop_str = f" {{{prop_parts}}}"
        query = (
            f"MATCH (a:{from_label} {{{from_key}: $from_val}}) "
            f"MATCH (b:{to_label} {{{to_key}: $to_val}}) "
            f"MERGE (a)-[r:{rel_type}{prop_str}]->(b) "
            f"RETURN r"
        )
        params = {"from_val": from_value, "to_val": to_value, **props}
        return CypherQuery(query=query, params=params)

    @staticmethod
    def batch_merge_relationships(
        from_label: str, from_key: str,
        to_label: str, to_key: str,
        rel_type: str, records: list[dict]
    ) -> CypherQuery:
        """Build a batch MERGE query for multiple relationships using UNWIND."""
        query = (
            f"UNWIND $records AS rec "
            f"MATCH (a:{from_label} {{{from_key}: rec.from_val}}) "
            f"MATCH (b:{to_label} {{{to_key}: rec.to_val}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            f"RETURN count(r) AS count"
        )
        return CypherQuery(query=query, params={"records": records})

    @staticmethod
    def delete_relationships(
        from_label: str, from_key: str, from_value,
        rel_type: str
    ) -> CypherQuery:
        """Delete all relationships of a type from a node."""
        query = (
            f"MATCH (a:{from_label} {{{from_key}: $from_val}})-[r:{rel_type}]->() "
            f"DELETE r"
        )
        return CypherQuery(query=query, params={"from_val": from_value})

    @staticmethod
    def get_neighbors(element_id: str, direction: str = "both", limit: int = 50) -> CypherQuery:
        """Build a query to get neighbors of a node."""
        if direction == "outgoing":
            pattern = "(n)-[r]->(m)"
        elif direction == "incoming":
            pattern = "(n)<-[r]-(m)"
        else:
            pattern = "(n)-[r]-(m)"
        query = (
            f"MATCH {pattern} WHERE elementId(n) = $element_id "
            f"RETURN m, type(r) AS rel_type, labels(m) AS labels, elementId(m) AS eid "
            f"LIMIT $limit"
        )
        return CypherQuery(query=query, params={"element_id": element_id, "limit": limit})


class AnalyticsBuilder:
    """Builds Cypher queries for graph analytics."""

    @staticmethod
    def graph_statistics(repo_uid: str) -> CypherQuery:
        """Get node and relationship counts for a repository."""
        query = (
            "MATCH (r:Repository {uid: $repo_uid}) "
            "OPTIONAL MATCH (r)-[*1..4]-(n) "
            "WITH r, collect(DISTINCT n) AS nodes "
            "WITH nodes + [r] AS all_nodes "
            "UNWIND all_nodes AS n "
            "WITH n, labels(n) AS lbls "
            "WHERE size(lbls) > 0 "
            "RETURN lbls[0] AS label, count(DISTINCT n) AS count "
            "ORDER BY count DESC"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid})

    @staticmethod
    def most_connected_files(repo_uid: str, limit: int = 10) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid})-[:CONTAINS*]->(f:File) "
            "OPTIONAL MATCH (f)-[rel]-() "
            "WITH f, count(rel) AS connections "
            "RETURN f.path AS path, f.language AS language, connections "
            "ORDER BY connections DESC "
            "LIMIT $limit"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid, "limit": limit})

    @staticmethod
    def largest_classes(repo_uid: str, limit: int = 10) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid})-[:CONTAINS*]->(:File)-[:DEFINES]->(c:Class) "
            "OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method) "
            "WITH c, count(m) AS method_count "
            "RETURN c.name AS name, c.file_path AS file_path, method_count "
            "ORDER BY method_count DESC "
            "LIMIT $limit"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid, "limit": limit})

    @staticmethod
    def dependency_graph(repo_uid: str) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid})-[:DEPENDS_ON]->(d:Dependency) "
            "OPTIONAL MATCH (f:File)-[:DEPENDS_ON]->(d) "
            "RETURN coalesce(f.path, d.source_file, 'package.json') AS file_path, d.name AS dependency, d.version AS version"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid})

    @staticmethod
    def import_graph(repo_uid: str) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid})-[:CONTAINS*]->(f:File)-[:IMPORTS]->(i:Import) "
            "RETURN f.path AS file_path, i.module AS module, i.name AS name"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid})

    @staticmethod
    def call_graph(repo_uid: str) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid}) "
            "MATCH (caller)-[:CALLS]->(callee) "
            "WHERE (r)-[*1..3]-(caller) AND (r)-[*1..3]-(callee) "
            "RETURN caller.name AS caller, labels(caller)[0] AS caller_type, "
            "callee.name AS callee, labels(callee)[0] AS callee_type"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid})

    @staticmethod
    def subgraph(repo_uid: str, limit: int = 70, filter_label: str | None = None) -> CypherQuery:
        """Get nodes and relationships for visual graph exploration."""
        if filter_label:
            query = (
                "MATCH (r:Repository {uid: $repo_uid}) "
                "MATCH (r)-[*1..3]-(n) "
                f"WHERE $filter_label IN labels(n) "
                "WITH r, collect(DISTINCT n)[..$limit] AS ns "
                "WITH ns + [r] AS node_list "
                "UNWIND node_list AS a "
                "OPTIONAL MATCH (a)-[rel]->(b) "
                "WHERE b IN node_list "
                "RETURN "
                "  collect(DISTINCT { "
                "    id: a.uid, "
                "    element_id: elementId(a), "
                "    label: labels(a)[0], "
                "    labels: labels(a), "
                "    name: coalesce(a.name, a.path, a.uid), "
                "    properties: properties(a) "
                "  }) AS nodes, "
                "  [r IN collect(DISTINCT rel) WHERE r IS NOT NULL | { "
                "    id: elementId(r), "
                "    source: startNode(r).uid, "
                "    target: endNode(r).uid, "
                "    type: type(r), "
                "    properties: properties(r) "
                "  }] AS edges"
            )
            params = {"repo_uid": repo_uid, "limit": limit, "filter_label": filter_label}
        else:
            query = (
                "MATCH (r:Repository {uid: $repo_uid}) "
                "MATCH (r)-[*1..2]-(n) "
                "WITH r, collect(DISTINCT n)[..$limit] AS ns "
                "WITH ns + [r] AS node_list "
                "UNWIND node_list AS a "
                "OPTIONAL MATCH (a)-[rel]->(b) "
                "WHERE b IN node_list "
                "RETURN "
                "  collect(DISTINCT { "
                "    id: a.uid, "
                "    element_id: elementId(a), "
                "    label: labels(a)[0], "
                "    labels: labels(a), "
                "    name: coalesce(a.name, a.path, a.uid), "
                "    properties: properties(a) "
                "  }) AS nodes, "
                "  [r IN collect(DISTINCT rel) WHERE r IS NOT NULL | { "
                "    id: elementId(r), "
                "    source: startNode(r).uid, "
                "    target: endNode(r).uid, "
                "    type: type(r), "
                "    properties: properties(r) "
                "  }] AS edges"
            )
            params = {"repo_uid": repo_uid, "limit": limit}
        return CypherQuery(query=query, params=params)

    @staticmethod
    def language_statistics(repo_uid: str) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid})-[:CONTAINS*]->(f:File) "
            "WHERE f.language IS NOT NULL "
            "RETURN f.language AS language, count(f) AS file_count "
            "ORDER BY file_count DESC"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid})

    @staticmethod
    def framework_statistics(repo_uid: str) -> CypherQuery:
        query = (
            "MATCH (r:Repository {uid: $repo_uid})-[:USES]->(fw:Framework) "
            "RETURN fw.name AS name, fw.version AS version, fw.confidence AS confidence"
        )
        return CypherQuery(query=query, params={"repo_uid": repo_uid})
