#!/bin/bash
# AutoDocOps Backup Script
# Usage: ./scripts/backup.sh [backup_dir]

set -euo pipefail

BACKUP_DIR="${1:-./backups/$(date +%Y%m%d_%H%M%S)}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-autodocops-postgres}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-autodocops-neo4j}"
REDIS_CONTAINER="${REDIS_CONTAINER:-autodocops-redis}"

mkdir -p "$BACKUP_DIR"
echo "=== AutoDocOps Backup ==="
echo "Backup directory: $BACKUP_DIR"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# PostgreSQL backup
echo "[1/3] Backing up PostgreSQL..."
docker exec "$POSTGRES_CONTAINER" pg_dump -U autodocops -Fc autodocops > "$BACKUP_DIR/postgres.dump"
echo "  PostgreSQL backup: $(du -h "$BACKUP_DIR/postgres.dump" | cut -f1)"

# Neo4j backup
echo "[2/3] Backing up Neo4j..."
docker exec "$NEO4J_CONTAINER" neo4j-admin database dump neo4j --to-path=/tmp/ 2>/dev/null || true
docker cp "$NEO4J_CONTAINER:/tmp/neo4j.dump" "$BACKUP_DIR/neo4j.dump" 2>/dev/null || echo "  Neo4j backup skipped (community edition)"

# Redis backup
echo "[3/3] Backing up Redis..."
docker exec "$REDIS_CONTAINER" redis-cli BGSAVE
sleep 2
docker cp "$REDIS_CONTAINER:/data/dump.rdb" "$BACKUP_DIR/redis.rdb" 2>/dev/null || echo "  Redis backup: RDB not found"

# Create manifest
cat > "$BACKUP_DIR/manifest.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "0.1.0",
  "components": {
    "postgres": "postgres.dump",
    "neo4j": "neo4j.dump",
    "redis": "redis.rdb"
  }
}
EOF

echo ""
echo "=== Backup complete ==="
echo "Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "Location: $BACKUP_DIR"
