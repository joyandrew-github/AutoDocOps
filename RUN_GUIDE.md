# AutoDocOps — Complete Run Guide 🚀

This guide provides step-by-step instructions to start, run, and develop the **AutoDocOps** platform.

---

## 📌 Prerequisites

Before starting, ensure you have:
* **Docker Desktop** installed and running.
* **Node.js** (v18+) and **Python** (3.11+) installed (if running locally without Docker).

---

## ⚡ Method 1: Quick Start with Docker (Recommended)

All services (Frontend, Backend, PostgreSQL, Redis, Neo4j) are containerized and pre-configured.

### 1. Start All Services
Open a terminal in the project root directory (`d:\AutoDocOps`) and run:
```powershell
docker compose up -d
```

### 2. Verify Services Are Running
```powershell
docker ps
```
You should see 5 running containers:
* `autodocops-frontend` (Port `3000`)
* `autodocops-backend` (Port `8001`)
* `autodocops-postgres` (Port `5432`)
* `autodocops-redis` (Port `6379`)
* `autodocops-neo4j` (Ports `7474`, `7687`)

---

## 🌐 Access Points & Web URLs

| Application / Service | URL / Port | Description |
|---|---|---|
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Main user interface, architecture diagrams, docs |
| **Backend API (Swagger Docs)** | [http://localhost:8001/docs](http://localhost:8001/docs) | Interactive FastAPI OpenAPI documentation |
| **Backend API Health** | [http://localhost:8001/health](http://localhost:8001/health) | Health check endpoint |
| **Neo4j Browser UI** | [http://localhost:7474](http://localhost:7474) | Graph database explorer (`neo4j` / `neo4j_password`) |
| **PostgreSQL Database** | `localhost:5432` | DB: `autodocops`, User: `autodocops`, Pass: `autodocops_password` |
| **Redis Cache** | `localhost:6379` | In-memory queue & caching |

---

## 🔑 Default Login Credentials

If prompted to log in at [http://localhost:3000/login](http://localhost:3000/login):
* **Username / Email:** `admin` or `admin@autodocops.local`
* **Password:** Any password (or register a new user at [http://localhost:3000/register](http://localhost:3000/register))

---

## 📖 How to Use AutoDocOps Features

### 1. Explore Repositories
* Navigate to **[http://localhost:3000/repositories](http://localhost:3000/repositories)**.
* View all connected repositories (`Abinexis_Backend`, `eduvizbackend`, etc.).
* Click **"Analyze & Parse"** to re-index any repository or **"Sync Now"** to pull the latest GitHub commits.

### 2. View Architecture Intelligence
* Navigate to **[http://localhost:3000/architecture](http://localhost:3000/architecture)**.
* Use the **Repository Dropdown** at the top right to switch between your repositories.
* Switch tabs to inspect:
  * **Architecture Layers:** Real file groupings (`API`, `MODEL`, `CONFIG`).
  * **Dependencies:** Interactive module and file dependency trees.
  * **Call Graph:** Live function execution and invocation chains.
  * **Components:** Subsystems and boundaries.
  * **Violations:** Architectural circular dependency checks.
* Click **"Export Diagram"** to download the Mermaid (`.mmd`) diagram file.

### 3. Browse & Export Documentation
* Navigate to **[http://localhost:3000/docs](http://localhost:3000/docs)**.
* Use the **Repository Dropdown** to select a repository.
* Click **"Read Full Doc"** on any document (like `eduvizbackend — Overview`, `authController.js`, `models/Product.js`) to view full Markdown tables and references.
* Click **"Download .md"** to save individual documentation files.
* Click **"Export All"** to download the complete repository documentation bundle in one file.

### 4. Connect a New GitHub Repository
1. Go to **[http://localhost:3000/settings](http://localhost:3000/settings)**.
2. In the GitHub tab, paste your repository URL (e.g. `https://github.com/your-username/your-repo`).
3. AutoDocOps will automatically:
   * Clone the codebase.
   * Scan files and detect frameworks/dependencies.
   * Parse all AST code nodes using Tree-sitter.
   * Generate 24 architecture diagrams.
   * Auto-generate complete developer documentation.

---

## 🛠️ Useful Docker Management Commands

### Stop All Services
```powershell
docker compose down
```

### Restart Specific Services
```powershell
# Restart Backend
docker restart autodocops-backend

# Restart Frontend
docker restart autodocops-frontend
```

### View Live Logs
```powershell
# View Backend logs
docker logs -f autodocops-backend

# View Frontend logs
docker logs -f autodocops-frontend
```

### Run Database Migrations (If Models Change)
```powershell
docker exec autodocops-backend alembic upgrade head
```

---

## 💻 Method 2: Running Locally Without Docker (For Development)

If you prefer to run services natively on your host machine:

### 1. Backend (FastAPI + Python 3.11)
```powershell
# Navigate to backend
cd d:\AutoDocOps\backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run Uvicorn dev server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Frontend (Next.js 14)
```powershell
# Navigate to frontend
cd d:\AutoDocOps\frontend

# Run Next.js dev server
npm run dev
```
*(Ensure PostgreSQL, Redis, and Neo4j are running via Docker or local installations).*

---

## 🎯 Summary Checklist for Tomorrow

1. Open PowerShell / Terminal in `d:\AutoDocOps`.
2. Run `docker compose up -d`.
3. Open browser to **[http://localhost:3000](http://localhost:3000)**.
4. Everything is ready and persisted in the Docker database volumes!
