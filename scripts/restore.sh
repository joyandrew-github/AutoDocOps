#!/bin/bash
# AutoDocOps Restore Script
# Usage: ./scripts/restore.sh <backup_dir>

set -euo pipefail

BACKUP_DIR="${1:?Usage: ./scripts/restore.sh <backup_dir>}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-autodocops-postgres}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-autodocops-neo4j}"
REDIS_CONTAINER="${REDIS_CONTAINER:-autodocops-redis}"

if [ ! -f "$BACKUP_DIR/manifest.json" ]; then
    echo "ERROR: manifest.json not found in $BACKUP_DIR"
    exit 1
fi

echo "=== AutoDocOps Restore ==="
echo "Restoring from: $BACKUP_DIR"
echo "Manifest:"
cat "$BACKUP_DIR/manifest.json"
echo ""

read -p "This will OVERWRITE current data. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# PostgreSQL restore
if [ -f "$BACKUP_DIR/postgres.dump" ]; then
    echo "[1/3] Restoring PostgreSQL..."
    docker exec -i "$POSTGRES_CONTAINER" pg_restore -U autodocops -d autodocops --clean --if-exists < "$BACKUP_DIR/postgres.dump" || true
    echo "  PostgreSQL restored."
else
    echo "[1/3] PostgreSQL backup not found, skipping."
fi

# Neo4j restore
if [ -f "$BACKUP_DIR/neo4j.dump" ]; then
    echo "[2/3] Restoring Neo4j..."
    docker cp "$BACKUP_DIR/neo4j.dump" "$NEO4J_CONTAINER:/tmp/neo4j.dump"
    docker exec "$NEO4J_CONTAINER" neo4j-admin database load neo4j --from-path=/tmp/ --overwrite-destination=true 2>/dev/null || echo "  Neo4j restore skipped (community edition)"
else
    echo "[2/3] Neo4j backup not found, skipping."
fi

# Redis restore
if [ -f "$BACKUP_DIR/redis.rdb" ]; then
    echo "[3/3] Restoring Redis..."
    docker cp "$BACKUP_DIR/redis.rdb" "$REDIS_CONTAINER:/data/dump.rdb"
    docker restart "$REDIS_CONTAINER"
    echo "  Redis restored."
else
    echo "[3/3] Redis backup not found, skipping."
fi

echo ""
echo "=== Restore complete ==="
echo "Please verify all services are healthy: curl http://localhost:8000/api/v1/health"
