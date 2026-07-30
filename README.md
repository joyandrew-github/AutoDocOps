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
- **Tree-sitter** - Incremental parsing system for source code analysis

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
│   │   │   │   ├── repositories.py    # Repository Intelligence API
│   │   │   │   ├── parser.py          # Parser Engine API
│   │   │   │   ├── memory.py          # Repository Memory Engine API
│   │   │   │   ├── graph.py           # Knowledge Graph Engine API
│   │   │   │   ├── search.py          # Vector Search & Semantic Retrieval API
│   │   │   │   └── documentation.py   # Intelligent Documentation Engine API
│   │   │   └── api.py                 # API router
│   │   ├── core/
│   │   │   ├── config.py              # Application settings
│   │   │   ├── logging.py             # Loguru logging
│   │   │   └── security.py            # Security utilities
│   │   ├── db/
│   │   │   ├── base.py, session.py    # SQLAlchemy base & session
│   │   │   ├── neo4j.py               # Neo4j client
│   │   │   └── redis.py               # Redis client
│   │   ├── engines/parser_engine/
│   │   │   ├── base_parser.py         # Abstract base parser
│   │   │   ├── parser_router.py       # Language parser router
│   │   │   ├── python_parser.py       # Python Tree-sitter parser
│   │   │   ├── javascript_parser.py   # JavaScript Tree-sitter parser
│   │   │   ├── typescript_parser.py   # TypeScript Tree-sitter parser
│   │   │   └── parser_service.py      # Parser orchestration service
│   │   ├── engines/memory_engine/
│   │   │   ├── diff_engine.py         # Snapshot comparison & change detection
│   │   │   ├── commit_tracker.py      # Git commit history tracking
│   │   │   └── snapshot_service.py    # Snapshot creation & management
│   │   ├── engines/graph_engine/
│   │   │   ├── cypher_builder.py       # Reusable Cypher query builders
│   │   │   ├── graph_sync_service.py   # PostgreSQL→Neo4j synchronization
│   │   │   └── graph_query_service.py  # Read-only graph analytics
│   │   ├── engines/vector_engine/
│   │   │   ├── embedding_providers.py  # Pluggable embedding providers
│   │   │   ├── chunker.py             # Semantic code chunking
│   │   │   ├── embedding_service.py   # Incremental embedding sync
│   │   │   └── search_service.py      # Cosine similarity search
│   │   ├── engines/documentation_engine/
│   │   │   ├── markdown_generator.py  # Markdown document generation
│   │   │   └── documentation_service.py # Incremental documentation pipeline
│   │   ├── engines/architecture_engine/
│   │   │   ├── analyzer.py            # Architecture analysis (layers, modules, dependencies, violations)
│   │   │   ├── diagram_generator.py   # PlantUML, Mermaid, JSON, SVG export
│   │   │   └── architecture_service.py # Incremental architecture pipeline
│   │   ├── engines/impact_engine/
│   │   │   └── impact_service.py       # Impact analysis, risk scoring, test recommendations
│   │   ├── engines/ai_engine/
│   │   │   ├── base.py                # BaseAgent, AgentContext, ConversationMemory
│   │   │   ├── tools.py               # ToolExecutor (calls existing services)
│   │   │   ├── agents.py              # 7 specialized agents
│   │   │   └── orchestrator.py        # AgentOrchestrator, AgentRegistry
│   │   ├── models/
│   │   │   ├── user.py                # User model
│   │   │   ├── repository.py          # Repository, Scan, File, Language, Framework, Dependency
│   │   │   ├── parser.py              # ASTNode, Function, Class, Method, Import, Export, Variable, Comment, ParserRun
│   │   │   ├── memory.py              # GitCommit, RepositorySnapshot, EntityVersion, ChangeSet, FileChange, EntityChange
│   │   │   ├── vector.py              # Embedding, CodeChunk, SearchIndex, EmbeddingJob
│   │   │   ├── documentation.py       # Documentation, DocumentationVersion, DocumentationSection, DocumentationJob
│   │   │   ├── architecture.py        # ArchitectureModel, ArchitectureDiagram, ArchitectureSnapshot, ArchitectureViolation
│   │   │   └── impact.py              # ImpactAnalysis, ImpactResult, ImpactRelationship, RiskAssessment
│   │   ├── schemas/
│   │   │   ├── repository.py          # Repository Pydantic schemas
│   │   │   ├── parser.py              # Parser Pydantic schemas
│   │   │   ├── memory.py              # Memory Engine Pydantic schemas
│   │   │   ├── graph.py               # Graph Engine Pydantic schemas
│   │   │   ├── vector.py              # Vector Search Pydantic schemas
│   │   │   ├── documentation.py       # Documentation Engine Pydantic schemas
│   │   │   ├── architecture.py        # Architecture Engine Pydantic schemas
│   │   │   ├── impact.py              # Impact Analysis Pydantic schemas
│   │   │   └── ai.py                  # AI Multi-Agent System Pydantic schemas
│   │   ├── services/
│   │   │   ├── git_manager.py         # Git clone/pull operations
│   │   │   ├── repository_scanner.py  # File scanning & metadata collection
│   │   │   └── repository_service.py  # Repository business logic
│   │   ├── repositories/
│   │   │   ├── repository_repo.py     # Repository data access
│   │   │   ├── parser_repo.py         # Parser data access
│   │   │   ├── memory_repo.py         # Memory Engine data access
│   │   │   ├── vector_repo.py         # Vector Search data access
│   │   │   ├── documentation_repo.py  # Documentation Engine data access
│   │   │   ├── architecture_repo.py   # Architecture Engine data access
│   │   │   └── impact_repo.py         # Impact Analysis data access
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

## Parser Engine

The Parser Engine uses Tree-sitter to parse source code into structured Abstract Syntax Trees (ASTs) for deep code analysis.

### Features

- **Tree-sitter Integration** — Incremental parsing system for accurate, efficient source code analysis
- **Multi-Language Support** — Python, JavaScript, TypeScript (extensible architecture for Java, C++, Go, Rust)
- **AST Extraction** — Functions, Classes, Methods, Imports, Exports, Variables, Comments
- **Detailed Metadata** — Line numbers, parameters, return types, decorators, inheritance, docstrings
- **Parallel Parsing** — Multi-threaded file parsing for performance
- **Parser Router** — Automatic language-based parser selection
- **Extensible Design** — Easy to add new language parsers

### Supported Languages

| Language | Features |
|----------|----------|
| Python | Functions, Classes, Methods, Imports, Variables, Comments, Decorators, Docstrings, Async/Generator |
| JavaScript | Functions (declaration, expression, arrow), Classes, Methods, Imports (ES6, require), Exports, Variables, Comments |
| TypeScript | All JavaScript features + Type annotations, Interfaces, Abstract classes, Enums, Type aliases |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/{id}/parse` | Parse all supported files in a repository |
| `GET` | `/api/v1/repositories/{id}/ast` | Get AST summary for a repository |
| `GET` | `/api/v1/repositories/{id}/functions` | Get all extracted functions |
| `GET` | `/api/v1/repositories/{id}/classes` | Get all extracted classes |
| `GET` | `/api/v1/repositories/{id}/imports` | Get all extracted imports |
| `GET` | `/api/v1/repositories/{id}/variables` | Get all extracted variables |

### Usage Example

```bash
# Parse a repository (must be scanned first)
curl -X POST http://localhost:8000/api/v1/repositories/1/parse

# Get AST summary
curl http://localhost:8000/api/v1/repositories/1/ast

# Get specific node types
curl http://localhost:8000/api/v1/repositories/1/functions
curl http://localhost:8000/api/v1/repositories/1/classes
curl http://localhost:8000/api/v1/repositories/1/imports
curl http://localhost:8000/api/v1/repositories/1/variables
```

### Running Tests

```bash
cd backend
pytest tests/ -v
```

## Repository Memory Engine

The Repository Memory Engine tracks repository evolution across Git commits and preserves historical knowledge by detecting changes at both the file level and code entity level.

### Features

- **Git History Tracking** — Syncs commit history (hash, parent, author, timestamp, message, branch, tags) via GitPython
- **Repository Snapshots** — Creates point-in-time snapshots with aggregated metrics (files, classes, functions, methods, imports, variables)
- **Entity Versioning** — Tracks versions of classes, functions, methods, variables, imports, and exports across commits
- **Change Detection** — Detects new, deleted, renamed, modified, and moved files and entities using the DiffEngine
- **DiffEngine** — Reusable comparison engine that generates structured change objects from snapshot data
- **Performance** — Processes only changed files, reuses incremental parsing information
- **Error Handling** — Continues processing if individual comparisons fail, records failures

### Change Types Detected

| Level | Change Types |
|-------|--------------|
| **File** | added, modified, deleted, renamed |
| **Entity** | added, modified, deleted, renamed, moved |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/repositories/{id}/timeline` | Chronological timeline of commits, snapshots, and changes |
| `GET` | `/api/v1/repositories/{id}/commits` | Commit history for a repository |
| `GET` | `/api/v1/repositories/{id}/snapshots` | Repository snapshots over time |
| `GET` | `/api/v1/repositories/{id}/changes` | Change sets between snapshots |
| `GET` | `/api/v1/repositories/{id}/changes/{commit}` | Detailed file and entity changes for a specific commit |

### Usage Example

```bash
# Get repository timeline
curl http://localhost:8000/api/v1/repositories/1/timeline

# Get commit history
curl http://localhost:8000/api/v1/repositories/1/commits

# Get snapshots
curl http://localhost:8000/api/v1/repositories/1/snapshots

# Get all change sets
curl http://localhost:8000/api/v1/repositories/1/changes

# Get changes for a specific commit
curl http://localhost:8000/api/v1/repositories/1/changes/abc123def456
```

## Knowledge Graph Engine

The Knowledge Graph Engine builds a Neo4j-powered Software Knowledge Graph representing the complete repository structure and relationships.

### Features

- **Neo4j Graph Builder** — Synchronizes PostgreSQL parsed entities into Neo4j on every snapshot
- **Incremental Updates** — Never rebuilds the graph; only creates, updates, or deletes changed nodes and relationships
- **Reusable Cypher Layer** — Parameterized Cypher query builders (NodeBuilder, RelationshipBuilder, AnalyticsBuilder)
- **Graph Analytics** — Most connected files, largest classes, dependency graph, import graph, call graph, language & framework statistics
- **Batch Writes** — All Neo4j writes are batched using UNWIND for performance
- **Error Handling** — If one node fails, remaining nodes continue syncing

### Node Types

Repository, Commit, Snapshot, Directory, File, Class, Function, Method, Variable, Import, Export, Interface, Enum, Dependency, Framework, ProgrammingLanguage

### Relationship Types

| Relationship | From | To |
|---|---|---|
| CONTAINS | Repository/Directory/Snapshot | Directory/File |
| DEFINES | File | Class/Function/Method/Variable/Import/Export |
| HAS_METHOD | Class | Method |
| IMPORTS | File | Import |
| DEPENDS_ON | Repository/File | Dependency |
| EXTENDS | Class | Class |
| IMPLEMENTS | Class | Interface |
| HAS_COMMIT | Repository | Commit |
| CREATED | Commit | Snapshot |
| USES | Repository | Framework |
| USES_LANGUAGE | Repository | ProgrammingLanguage |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/{id}/graph/sync` | Sync repository to Neo4j graph |
| `GET` | `/api/v1/repositories/{id}/graph/statistics` | Node and relationship counts |
| `GET` | `/api/v1/repositories/{id}/graph/node/{element_id}` | Get a specific graph node |
| `GET` | `/api/v1/repositories/{id}/graph/neighbors/{element_id}` | Get neighbors of a node |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/connected-files` | Most connected files |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/largest-classes` | Largest classes by method count |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/dependency-graph` | File-to-dependency relationships |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/import-graph` | File-to-import relationships |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/call-graph` | Function/method call relationships |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/languages` | Language distribution |
| `GET` | `/api/v1/repositories/{id}/graph/analytics/frameworks` | Detected frameworks |

### Usage Example

```bash
# Sync repository to Neo4j
curl -X POST http://localhost:8000/api/v1/repositories/1/graph/sync

# Get graph statistics
curl http://localhost:8000/api/v1/repositories/1/graph/statistics

# Get most connected files
curl http://localhost:8000/api/v1/repositories/1/graph/analytics/connected-files

# Get dependency graph
curl http://localhost:8000/api/v1/repositories/1/graph/analytics/dependency-graph

# Get call graph
curl http://localhost:8000/api/v1/repositories/1/graph/analytics/call-graph
```

## Vector Search & Semantic Retrieval Engine

The Vector Search Engine provides production-grade semantic code search powered by PostgreSQL pgvector.

### Features

- **Pluggable Embedding Providers** — `MockEmbeddingProvider`, `OpenAIEmbeddingProvider`, `LocalEmbeddingProvider` with a common `BaseEmbeddingProvider` interface
- **Semantic Chunking** — Splits large code entities into meaningful chunks respecting line boundaries
- **Incremental Embeddings** — Only processes new/modified entities; deletes embeddings for removed entities via Memory Engine
- **Cosine Similarity Search** — Top-K semantic search with repository, language, and entity type filtering
- **Background Job Tracking** — `EmbeddingJob` records track progress, retries, and failures
- **Batch Processing** — Configurable batch sizes for embedding generation

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_PROVIDER` | `mock` | Provider: `mock`, `openai`, `local` |
| `EMBEDDING_DIMENSION` | `1536` | Embedding vector dimension |
| `OPENAI_API_KEY` | `""` | OpenAI API key (required for `openai` provider) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI model |
| `EMBEDDING_BATCH_SIZE` | `100` | Entities per batch |
| `CHUNK_SIZE` | `512` | Tokens per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap tokens between chunks |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/{id}/embeddings/sync` | Generate/update embeddings |
| `POST` | `/api/v1/search` | Semantic code search |
| `GET` | `/api/v1/search/file/{file_id}` | Search by file |
| `GET` | `/api/v1/search/function/{function_id}` | Search by function |
| `GET` | `/api/v1/search/similar/{entity_name}` | Find similar entities |
| `GET` | `/api/v1/repositories/{id}/embeddings/status` | Index status |
| `GET` | `/api/v1/repositories/{id}/embeddings/jobs` | Job history |

### Usage Example

```bash
# Sync embeddings for a repository
curl -X POST http://localhost:8000/api/v1/repositories/1/embeddings/sync

# Semantic search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "function that processes user input", "repository_id": 1, "top_k": 5}'

# Find similar entities
curl http://localhost:8000/api/v1/search/similar/process?repository_id=1&entity_type=function

# Check index status
curl http://localhost:8000/api/v1/repositories/1/embeddings/status
```

## Intelligent Documentation Engine

The Documentation Engine automatically generates and maintains developer documentation from source code and repository intelligence.

### Documentation Types

- **Repository Overview** — Project summary with stats, languages, frameworks, dependencies
- **File Documentation** — Per-file docs with classes, functions, imports, variables
- **Class Documentation** — Standalone class docs with methods and inheritance
- **Function Documentation** — Function docs with signature, parameters, returns, decorators
- **Module Documentation** — Folder/package docs aggregating contained entities
- **Changelog** — Commit history summary from Repository Memory Engine
- **Onboarding Guide** — Developer getting-started guide with tech stack and key files
- **Dependency Documentation** — Full dependency listing with versions and package managers

### Features

- **Incremental Generation** — Only regenerates docs for new/modified/deleted entities via Memory Engine
- **Versioning** — Tracks documentation versions with change history
- **Sections** — Structured sections within each document
- **Export Formats** — Markdown, HTML, PDF-ready Markdown
- **Search** — Full-text search across all documentation
- **Batch Processing** — Generates all doc types in a single pipeline pass

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/{id}/documentation/generate` | Generate/update documentation |
| `GET` | `/api/v1/repositories/{id}/documentation` | List all documentation |
| `GET` | `/api/v1/documentation/{id}` | Get specific document with sections |
| `GET` | `/api/v1/documentation/search` | Search documentation |
| `POST` | `/api/v1/documentation/export` | Export in markdown/HTML/PDF format |

### Usage Example

```bash
# Generate all documentation
curl -X POST http://localhost:8000/api/v1/repositories/1/documentation/generate

# Generate specific types only
curl -X POST http://localhost:8000/api/v1/repositories/1/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"doc_types": ["repository_overview", "class", "function"]}'

# List all documentation
curl http://localhost:8000/api/v1/repositories/1/documentation

# Search documentation
curl "http://localhost:8000/api/v1/documentation/search?query=process&repository_id=1"

# Export as HTML
curl -X POST http://localhost:8000/api/v1/documentation/export \
  -H "Content-Type: application/json" \
  -d '{"repository_id": 1, "format": "html"}'
```

## Architecture Intelligence Engine

The Architecture Engine automatically generates software architecture views from repository intelligence.

### Architecture Analysis

- **Layer Analysis** — Identifies architectural layers (API, Service, Engine, Repository, Model, Schema, Util, Config)
- **Module Analysis** — Maps directory structure to logical modules with language breakdown
- **Component Analysis** — Groups classes and functions into logical components, identifies services and entry points
- **Dependency Graph** — File and module dependency analysis from import statements
- **Call Graph** — Function and method call graph with cross-module edges
- **Entry Points** — Identifies application entry points (main.py, app.py, create_app, etc.)
- **API Detection** — Identifies API endpoints from file paths and decorators

### Violation Detection

- **Circular Dependencies** — Detects circular import chains
- **Layer Violations** — Detects imports that violate layered architecture conventions

### Diagram Export

| Format | Description |
|--------|-------------|
| **Mermaid** | Mermaid.js diagram definitions |
| **PlantUML** | PlantUML diagram definitions |
| **JSON** | Structured JSON data |
| **SVG** | SVG-ready vector graphics |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/{id}/architecture/generate` | Generate architecture models and diagrams |
| `GET` | `/api/v1/repositories/{id}/architecture` | List all architecture models |
| `GET` | `/api/v1/architecture/{id}` | Get specific model with diagrams |
| `GET` | `/api/v1/repositories/{id}/architecture/dependencies` | Get dependency graph |
| `GET` | `/api/v1/repositories/{id}/architecture/callgraph` | Get call graph |
| `GET` | `/api/v1/repositories/{id}/architecture/violations` | Get architecture violations |

### Usage Example

```bash
# Generate architecture
curl -X POST http://localhost:8000/api/v1/repositories/1/architecture/generate

# List models
curl http://localhost:8000/api/v1/repositories/1/architecture

# Get dependency graph
curl http://localhost:8000/api/v1/repositories/1/architecture/dependencies

# Get call graph
curl http://localhost:8000/api/v1/repositories/1/architecture/callgraph

# Get violations
curl http://localhost:8000/api/v1/repositories/1/architecture/violations

# Get specific model with all diagram formats
curl http://localhost:8000/api/v1/architecture/1
```

## Impact Analysis Engine

The Impact Analysis Engine evaluates the impact of source code changes across the entire codebase.

### Change Impact Analysis

- **Direct Dependents** — Files and entities that directly import/use the changed entity
- **Indirect Dependents** — Transitive dependencies up to configurable depth
- **Call Graph Impact** — Functions and methods affected through the call chain
- **Import Impact** — Files affected through import relationships
- **API Impact** — Public API changes flagged with higher risk
- **Cross-Module Impact** — Changes that affect multiple modules

### Risk Assessment

Configurable risk scoring with weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Dependency** | 25% | Number of downstream dependencies |
| **API** | 20% | Public API surface changes |
| **Cross-Module** | 15% | Changes spanning multiple modules |
| **Circular Deps** | 15% | Involvement in circular dependency chains |
| **Change Frequency** | 10% | Historical change frequency |
| **Architecture** | 15% | Architecture-level impact |

Risk levels: **Low** (0–0.25) · **Medium** (0.25–0.50) · **High** (0.50–0.75) · **Critical** (0.75–1.0)

### Test Recommendations

- **Unit Tests** — For changed functions, methods, and classes
- **Integration Tests** — For entities with downstream dependents
- **Regression Tests** — For high/critical risk entities

### Export Formats

- **JSON** — Structured analysis data
- **Markdown** — Human-readable impact report
- **HTML** — Styled HTML report

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories/{id}/impact/analyze` | Run impact analysis |
| `GET` | `/api/v1/impact/{id}` | Get analysis with results and risk |
| `GET` | `/api/v1/repositories/{id}/impact/history` | Analysis history |
| `GET` | `/api/v1/repositories/{id}/impact/entity/{name}` | Entity-level impact |
| `GET` | `/api/v1/repositories/{id}/impact/risk` | Latest risk assessment |
| `POST` | `/api/v1/impact/{id}/export` | Export analysis (JSON/Markdown/HTML) |

### Usage Example

```bash
# Run impact analysis
curl -X POST http://localhost:8000/api/v1/repositories/1/impact/analyze

# Get analysis details
curl http://localhost:8000/api/v1/impact/1

# Get analysis history
curl http://localhost:8000/api/v1/repositories/1/impact/history

# Get entity-level impact
curl http://localhost:8000/api/v1/repositories/1/impact/entity/process

# Get risk assessment
curl http://localhost:8000/api/v1/repositories/1/impact/risk

# Export as Markdown
curl -X POST http://localhost:8000/api/v1/impact/1/export \
  -H "Content-Type: application/json" \
  -d '{"format": "markdown"}'
```

## AI Multi-Agent System

The AI layer coordinates specialized agents that consume existing AutoDocOps engines.

### Architecture

- **AgentOrchestrator** — Routes, plans, and executes agent workflows
- **AgentRegistry** — Manages available agents and confidence-based routing
- **BaseAgent** — Abstract base with `handle()`, `stream()`, and `can_handle()` methods
- **AgentContext** — Shared invocation state (repository, conversation, entities)
- **ToolExecutor** — 18 tool adapters that delegate to existing services
- **ConversationMemory** — Per-conversation history with context summaries

### Agents

| Agent | Description | Tools Used |
|-------|-------------|------------|
| **Repository Expert** | Repository questions, overview, commits | `get_repository`, `get_files`, `get_commits`, `search_code` |
| **Code Expert** | Explains functions, classes, modules | `get_functions`, `get_classes`, `get_imports`, `search_code` |
| **Documentation Expert** | Generates and retrieves docs | `get_documentation`, `generate_documentation` |
| **Architecture Expert** | Architecture, dependencies, diagrams | `get_architecture`, `get_dependencies`, `get_callgraph`, `get_violations` |
| **Impact Expert** | "What if I change X?" analysis | `analyze_impact`, `get_impact`, `get_risk` |
| **Search Expert** | Semantic code search | `search_code` |
| **Workflow Planner** | Breaks complex requests into subtasks | Routes to other agents |

### Execution Modes

- **Single-agent** — Auto-routed via confidence scoring
- **Multi-agent** — Sequential plan execution
- **Parallel** — Concurrent agent execution via thread pool
- **Streaming** — Incremental response streaming

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ai/chat` | Auto-routed single-agent chat |
| `POST` | `/api/v1/ai/plan` | Create execution plan |
| `POST` | `/api/v1/ai/execute` | Execute plan (sequential/parallel) |
| `GET` | `/api/v1/ai/history` | Conversation history |
| `GET` | `/api/v1/ai/agents` | List available agents |
| `POST` | `/api/v1/ai/stream` | Streaming response |

### Usage Example

```bash
# Chat (auto-routes to best agent)
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "explain the architecture", "repository_id": 1}'

# Create a plan
curl -X POST http://localhost:8000/api/v1/ai/plan \
  -H "Content-Type: application/json" \
  -d '{"message": "give me a full overview", "repository_id": 1}'

# Execute plan in parallel
curl -X POST http://localhost:8000/api/v1/ai/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "overview", "repository_id": 1, "parallel": true}'

# List agents
curl http://localhost:8000/api/v1/ai/agents

# Get conversation history
curl "http://localhost:8000/api/v1/ai/history?conversation_id=<id>"
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
