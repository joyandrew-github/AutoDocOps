# AutoDocOps

Production-grade AI platform for automated documentation operations.

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Python 3.12** - Programming language
- **PostgreSQL** - Relational database
- **Neo4j** - Graph database
- **Redis** - In-memory data store
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations

### Frontend
- **Next.js 14** - React framework
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework

### Infrastructure
- **Docker Compose** - Container orchestration
- **Make** - Build automation

## Project Structure

```
AutoDocOps/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py          # Health check endpoints
│   │   │   │   └── repositories.py    # Repository Intelligence API
│   │   │   └── api.py                 # API router
│   │   ├── core/
│   │   │   ├── config.py              # Application settings
│   │   │   ├── logging.py             # Loguru logging
│   │   │   └── security.py            # Security utilities
│   │   ├── db/
│   │   │   ├── base.py, session.py    # SQLAlchemy base & session
│   │   │   ├── neo4j.py               # Neo4j client
│   │   │   └── redis.py               # Redis client
│   │   ├── models/
│   │   │   ├── user.py                # User model
│   │   │   └── repository.py          # Repository, Scan, File, Language, Framework, Dependency
│   │   ├── schemas/
│   │   │   └── repository.py          # Request/response Pydantic schemas
│   │   ├── services/
│   │   │   ├── git_manager.py         # Git clone/pull operations
│   │   │   ├── repository_scanner.py  # File scanning & metadata collection
│   │   │   └── repository_service.py  # Business logic orchestration
│   │   ├── repositories/
│   │   │   └── repository_repo.py     # Data access layer
│   │   ├── utils/
│   │   │   ├── language_detector.py   # Extension-based language detection
│   │   │   ├── framework_detector.py  # Config-file framework detection
│   │   │   └── dependency_detector.py # Package manager dependency parsing
│   │   └── main.py                    # FastAPI application
│   ├── alembic/versions/              # Database migrations
│   ├── tests/                         # Unit tests
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Backend Docker image
│   └── .env                           # Environment variables
├── frontend/                          # Next.js frontend
├── docker-compose.yml                 # Docker Compose (all services)
├── Makefile                           # Development commands
└── README.md
```

## Prerequisites

- **Docker** and **Docker Compose** (for containerized development)
- **Python 3.12+** (for local backend development)
- **Node.js 20+** and **npm** (for local frontend development)
- **Make** (for using Makefile commands)

## Quick Start with Docker

The easiest way to get started is using Docker Compose:

```bash
# Build and start all services
make build
make up

# Or in one command
docker-compose up -d --build
```

This will start:
- PostgreSQL on port 5432
- Neo4j on ports 7474 (HTTP) and 7687 (Bolt)
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 3000

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- Neo4j Browser: http://localhost:7474

## Local Development Setup

### Backend Setup

1. **Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start PostgreSQL, Neo4j, and Redis:**
```bash
# Using Docker Compose for infrastructure services
docker-compose up -d postgres neo4j redis
```

4. **Run database migrations:**
```bash
cd backend
alembic upgrade head
```

5. **Start the backend server:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the Makefile:
```bash
make dev-backend
```

### Frontend Setup

1. **Install Node dependencies:**
```bash
cd frontend
npm install
```

2. **Configure environment variables:**
```bash
# .env.local is already configured for development
# Modify NEXT_PUBLIC_API_URL if needed
```

3. **Start the frontend development server:**
```bash
npm run dev
```

Or use the Makefile:
```bash
make dev-frontend
```

## Makefile Commands

The project includes a Makefile for common development tasks:

```bash
make help              # Show all available commands
make install           # Install all dependencies
make install-backend   # Install backend dependencies
make install-frontend  # Install frontend dependencies
make dev               # Run both backend and frontend
make dev-backend       # Run backend development server
make dev-frontend      # Run frontend development server
make build             # Build Docker containers
make up                # Start all services
make down              # Stop all services
make restart           # Restart all services
make logs              # Show logs from all services
make clean             # Remove containers, volumes, and networks
make test-backend      # Run backend tests
make lint-backend      # Run backend linting
make format-backend    # Format backend code
make migrate-db        # Run database migrations
make create-migration MSG="message"  # Create new migration
make rollback-db       # Rollback last migration
make psql               # Connect to PostgreSQL
make redis-cli          # Connect to Redis
```

## Environment Variables

### Backend Environment Variables

See `backend/.env.example` for all available variables:

- `APP_NAME` - Application name
- `DEBUG` - Debug mode (true/false)
- `POSTGRES_*` - PostgreSQL connection settings
- `NEO4J_*` - Neo4j connection settings
- `REDIS_*` - Redis connection settings
- `SECRET_KEY` - JWT secret key (change in production)
- `REPOSITORY_WORKSPACE` - Directory for cloned repositories
- `LOG_LEVEL` - Logging level (INFO, DEBUG, ERROR, etc.)

### Frontend Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL

## Database Migrations

### Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

Or using Makefile:
```bash
make create-migration MSG="description of changes"
```

### Apply migrations:
```bash
cd backend
alembic upgrade head
```

Or using Makefile:
```bash
make migrate-db
```

### Rollback migration:
```bash
cd backend
alembic downgrade -1
```

Or using Makefile:
```bash
make rollback-db
```

## Repository Intelligence Engine

The Repository Intelligence Engine analyzes any public or private Git repository to extract metadata, detect languages, frameworks, and dependencies.

### Features

- **Git Repository Management** — Clone/pull repositories via HTTPS
- **Recursive File Scanner** — Collects metadata (name, path, extension, language, size, modified time, SHA256 checksum) while ignoring `.git`, `node_modules`, `__pycache__`, `venv`, etc.
- **Language Detection** — Extension-based detection for 19+ languages (Python, Java, JavaScript, TypeScript, Go, Rust, C/C++, C#, HTML, CSS, SCSS, YAML, JSON, XML, Markdown, Shell, Dockerfile, Terraform)
- **Framework Detection** — Inspects config files to detect React, Next.js, Angular, Vue, Express, NestJS, Spring Boot, FastAPI, Flask, Django, Laravel, ASP.NET, Flutter
- **Dependency Extraction** — Parses `package.json`, `requirements.txt`, `pyproject.toml`, `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, `composer.json`, `pubspec.yaml`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/connect` | Connect a Git repository (clone or pull) |
| `POST` | `/api/v1/repositories/{id}/scan` | Scan a repository for files, languages, frameworks, dependencies |
| `GET` | `/api/v1/repositories` | List all connected repositories |
| `GET` | `/api/v1/repositories/{id}` | Get repository details with latest scan |
| `GET` | `/api/v1/repositories/{id}/files` | Get all scanned files |
| `GET` | `/api/v1/repositories/{id}/dependencies` | Get detected dependencies |
| `GET` | `/api/v1/repositories/{id}/frameworks` | Get detected frameworks |
| `GET` | `/api/v1/repositories/{id}/languages` | Get language statistics |

### Usage Example

```bash
# Connect a repository
curl -X POST http://localhost:8000/api/v1/repositories/connect \
  -H "Content-Type: application/json" \
  -d '{"repository_url": "https://github.com/owner/repo.git"}'

# Trigger a scan (use the returned repository id)
curl -X POST http://localhost:8000/api/v1/repositories/1/scan

# Get scan results
curl http://localhost:8000/api/v1/repositories/1/languages
curl http://localhost:8000/api/v1/repositories/1/frameworks
curl http://localhost:8000/api/v1/repositories/1/dependencies
curl http://localhost:8000/api/v1/repositories/1/files
```

### Running Tests

```bash
cd backend
pytest tests/ -v
```

## Health Checks

The application includes comprehensive health check endpoints:

- `GET /api/v1/health` - Comprehensive health check (PostgreSQL, Neo4j, Redis)
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## Logging

Logs are stored in `backend/logs/`:
- `app.log` - All application logs
- `error.log` - Error-level logs only

Logs are automatically rotated when they reach 10MB and retained for 30 days.

## Development Workflow

1. **Start infrastructure services:**
```bash
docker-compose up -d postgres neo4j redis
```

2. **Run backend and frontend locally:**
```bash
# Terminal 1
cd backend
uvicorn app.main:app --reload

# Terminal 2
cd frontend
npm run dev
```

3. **Or use Docker Compose for everything:**
```bash
docker-compose up --build
```

## Clean Architecture

The project follows clean architecture principles:

- **API Layer** (`app/api/`) - HTTP endpoints and routing
- **Core Layer** (`app/core/`) - Configuration, security, logging
- **Business Logic Layer** (`app/services/`) - Application logic
- **Data Access Layer** (`app/repositories/`) - Database operations
- **Models Layer** (`app/models/`) - SQLAlchemy models
- **Schemas Layer** (`app/schemas/`) - Pydantic schemas for validation

## Production Considerations

Before deploying to production:

1. **Change secrets:**
   - Update `SECRET_KEY` in backend `.env`
   - Update database passwords
   - Update Neo4j and Redis passwords

2. **Set DEBUG to false:**
   - Set `DEBUG=false` in backend `.env`

3. **Use environment-specific configurations:**
   - Create production `.env` files
   - Use environment variables in deployment

4. **Configure proper CORS origins:**
   - Update `BACKEND_CORS_ORIGINS` with production domains

5. **Set up proper logging:**
   - Configure log aggregation service
   - Set appropriate log levels

6. **Enable HTTPS:**
   - Use reverse proxy (nginx, traefik)
   - Configure SSL certificates

## Troubleshooting

### PostgreSQL connection issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Connect to PostgreSQL
make psql
```

### Neo4j connection issues
```bash
# Check if Neo4j is running
docker-compose ps neo4j

# View Neo4j logs
docker-compose logs neo4j

# Access Neo4j Browser
# Open http://localhost:7474 in your browser
```

### Redis connection issues
```bash
# Check if Redis is running
docker-compose ps redis

# View Redis logs
docker-compose logs redis

# Connect to Redis
make redis-cli
```

### Backend won't start
```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
cat backend/.env

# Check database connection
make psql
```

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on the project repository.
