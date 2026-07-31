# Deployment Guide

This guide covers production deployment of AutoDocOps v1.0.

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- Neo4j 5.x
- Redis 7.x
- Python 3.12+ (for local development)
- Node.js 20+ (for frontend builds)

## Quick Start with Docker Compose

```bash
# Clone repository
git clone https://github.com/yourorg/autodocops.git
cd autodocops

# Copy environment files
cp .env.example .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
db = SessionLocal()
admin = User(email='admin@example.com', username='admin', hashed_password=get_password_hash('changeme'), is_superuser=True)
db.add(admin)
db.commit()
print('Admin user created: admin@example.com / changeme')
"

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/v1
# API Docs: http://localhost:8000/api/docs
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_SERVER` | PostgreSQL host | localhost | Yes |
| `POSTGRES_PORT` | PostgreSQL port | 5432 | Yes |
| `POSTGRES_USER` | PostgreSQL user | autodocops | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | - | Yes |
| `POSTGRES_DB` | Database name | autodocops | Yes |
| `NEO4J_URI` | Neo4j bolt URI | bolt://localhost:7687 | Yes |
| `NEO4J_USER` | Neo4j username | neo4j | Yes |
| `NEO4J_PASSWORD` | Neo4j password | - | Yes |
| `REDIS_HOST` | Redis host | localhost | Yes |
| `REDIS_PORT` | Redis port | 6379 | Yes |
| `REDIS_PASSWORD` | Redis password | - | No |
| `SECRET_KEY` | JWT secret key | - | Yes |
| `ENVIRONMENT` | Environment | development | Yes |
| `EMBEDDING_PROVIDER` | Embedding provider | mock | No |
| `OPENAI_API_KEY` | OpenAI API key | - | If using OpenAI |

## Production Deployment

### Option 1: Kubernetes (Recommended)

```bash
# Build and push images
docker build -t your-registry/autodocops-backend:1.0 backend/
docker build -t your-registry/autodocops-frontend:1.0 frontend/
docker push your-registry/autodocops-backend:1.0
docker push your-registry/autodocops-frontend:1.0

# Deploy
kubectl apply -f k8s/
```

### Option 2: Docker Swarm

```bash
docker stack deploy autodocops -c docker-compose.prod.yml
```

### Option 3: Traditional VM

```bash
# Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm install
npm run build
npm run start:prod
```

## Database Migrations

```bash
# Generate migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Monitoring & Observability

- **Prometheus metrics**: `http://localhost:8000/metrics`
- **Health check**: `http://localhost:8000/api/v1/health`
- **OpenTelemetry traces**: Configure `OTEL_ENABLED=true` and `OTEL_EXPORTER_ENDPOINT`

## Security Considerations

1. Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
2. Enable HTTPS/TLS in production
3. Use environment-specific secrets (e.g., HashiCorp Vault)
4. Enable rate limiting (`RATE_LIMIT_PER_MINUTE`)
5. Configure CORS origins (`BACKEND_CORS_ORIGINS`)
6. Enable observability for security monitoring

## Scaling Recommendations

| Component | Horizontal Scaling | Vertical Scaling |
|-----------|-------------------|------------------|
| Backend API | Yes (stateless) | 4+ vCPU, 8GB+ RAM |
| Frontend | Yes (static) | 2 vCPU, 4GB RAM |
| PostgreSQL | Yes (read replicas) | 8+ vCPU, 32GB+ RAM |
| Neo4j | Yes (causal cluster) | 8+ vCPU, 32GB+ RAM |
| Redis | Yes (cluster mode) | 4 vCPU, 8GB RAM |

## Backup Strategy

```bash
# PostgreSQL backup
docker exec postgres pg_dump -U autodocops autodocops > backup.sql

# Neo4j backup
docker exec neo4j neo4j-admin database dump neo4j --to-path=/backups

# Redis backup
docker exec redis redis-cli BGSAVE
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.
