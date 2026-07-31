# AutoDocOps Architecture

## System Overview

AutoDocOps is a microservices-style platform built with Python (FastAPI) for the backend and Next.js for the frontend, using PostgreSQL, Neo4j, and Redis for data persistence.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ Dashboard│ │ Repos  │ │ AI Chat │ │ Docs    │ │ Integr. │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Layer (endpoints)                                   │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │  │
│  │  │ Auth │ │ Repos│ │ AI   │ │ Graph│ │ Integ│         │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │ Parser   │ │ Memory   │ │ Search   │ │ AI Engine│   │  │
│  │  │ Service  │ │ Service  │ │ Service  │ │          │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │ Docs     │ │ Arch     │ │ Impact   │ │ Integr.  │   │  │
│  │  │ Service  │ │ Service  │ │ Service  │ │ Service  │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Engine Layer                                            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │ Parser   │ │ Graph    │ │ Vector   │ │ GitHub   │   │  │
│  │  │ Engine   │ │ Engine   │ │ Services │ │ Engine   │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┐   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼────┐ ┌────▼────┐ ┌─────▼────┐
│ PostgreSQL  │ │  Neo4j  │ │  Redis   │
│ (Metadata)  │ │ (Graph) │ │ (Cache)  │
└─────────────┘ └─────────┘ └──────────┘
```

## Component Details

### Frontend (Next.js)
- **Framework**: Next.js 15 with App Router
- **UI Library**: shadcn/ui + TailwindCSS
- **State Management**: Zustand + React Query
- **Pages**: Dashboard, Repositories, AI Chat, Knowledge Graph, Documentation, Architecture, Impact Analysis, Search, Jobs, Integrations, Settings

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **ORM**: SQLAlchemy 2.0 with async
- **Authentication**: JWT with refresh tokens
- **Rate Limiting**: slowapi
- **Observability**: Prometheus + OpenTelemetry

### Engines

#### Parser Engine
- **Purpose**: Parse code files into AST nodes
- **Technology**: tree-sitter
- **Supported Languages**: Python, JavaScript/TypeScript, Java, Go, Rust, C#, PHP, Ruby, C/C++
- **Features**: Incremental parsing, checksum-based change detection

#### Graph Engine
- **Purpose**: Store and query code relationships
- **Technology**: Neo4j + Cypher
- **Features**: Node/relationship extraction, graph analytics, query builder

#### Vector Services
- **Purpose**: Generate embeddings for semantic search
- **Providers**: OpenAI, local, mock
- **Features**: Batch processing, similarity search

#### GitHub Engine
- **Purpose**: Handle GitHub webhooks and API interactions
- **Features**: Webhook processing, job queue, account management

### Services

#### AI Engine
- **Multi-Agent System**: Specialized agents for different tasks
- **Agents**: Repository Expert, Graph Expert, Documentation Expert, Architecture Expert, Impact Expert
- **Features**: Streaming responses, planning, tool execution

#### Integration Service
- **Connector Framework**: Extensible connector-based integration
- **Supported Services**: Jira, Azure DevOps, GitLab, Bitbucket, Slack, Teams, Confluence, ServiceNow
- **Features**: Retry policy, rate limiting, audit logging

## Data Flow

### Repository Sync Pipeline

```
GitHub Webhook → Celery Queue → GitHub Engine
                                            ↓
                                    Repository Scan
                                            ↓
                                    File Download
                                            ↓
                                    Parser Engine
                                            ↓
                                    AST Nodes (PostgreSQL)
                                            ↓
                                    Graph Sync Engine
                                            ↓
                                    Neo4j (Graph DB)
                                            ↓
                                    Embedding Sync
                                            ↓
                                    Vector Store (PostgreSQL)
                                            ↓
                                    Documentation Generation
                                            ↓
                                    Architecture Analysis
                                            ↓
                                    Impact Analysis
```

### AI Chat Flow

```
User Query → Frontend → API → AI Engine
                                    ↓
                            Agent Selection
                                    ↓
                            Tool Execution (optional)
                                    ↓
                            LLM Call → Streaming Response
                                    ↓
                            Frontend Display
```

### Integration Sync Flow

```
User Action → Frontend → API → Integration Service
                                    ↓
                            Connector Selection
                                    ↓
                            Rate Limiter
                                    ↓
                            Retry Policy
                                    ↓
                            External API Call
                                    ↓
                            Response Processing
                                    ↓
                            Audit Log
```

## Database Schema

### PostgreSQL Tables

- `users` — User accounts and authentication
- `repositories` — Repository metadata
- `repository_scans` — Scan history
- `repository_files` — File metadata
- `programming_languages` — Language statistics
- `frameworks` — Detected frameworks
- `dependencies` — Project dependencies
- `parser_runs` — Parser execution records
- `ast_nodes` — Functions, classes, methods, imports
- `git_commits` — Commit history
- `repository_snapshots` — Repository state snapshots
- `entity_versions` — Entity version history
- `changesets` — Change tracking
- `file_changes` — File-level changes
- `entity_changes` — Entity-level changes
- `integrations` — Integration configurations
- `integration_logs` — Integration audit logs

### Neo4j Graph

- **Nodes**: File, Function, Class, Method, Import, Export, Variable, Comment
- **Relationships**: CALLS, DEFINES, INHERITS, IMPLEMENTS, IMPORTS, EXPORTS, REFERENCES

## Security

- **Authentication**: JWT access tokens + refresh tokens
- **Password Hashing**: bcrypt
- **Rate Limiting**: Per-minute rate limits per IP
- **CORS**: Configurable allowed origins
- **SQL Injection**: Parameterized queries via SQLAlchemy
- **XSS**: React's built-in escaping
- **CSRF**: JWT-based authentication

## Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Kubernetes
kubectl apply -f k8s/

# Docker Swarm
docker stack deploy autodocops -c docker-compose.prod.yml
```

## Scalability

- **Backend**: Horizontal scaling (stateless)
- **Frontend**: Static files + CDN
- **PostgreSQL**: Read replicas
- **Neo4j**: Causal cluster
- **Redis**: Cluster mode
- **Celery**: Multiple workers

## Monitoring

- **Metrics**: Prometheus at `/metrics`
- **Health**: `/api/v1/health`
- **Tracing**: OpenTelemetry
- **Logs**: Structured JSON logs
