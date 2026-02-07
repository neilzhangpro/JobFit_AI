# JobFit AI — Operations Manual

This document provides step-by-step instructions for setting up, running, testing, and deploying the JobFit AI project.

---

## 1. Prerequisites

Ensure the following tools are installed on your development machine before proceeding.

| Tool | Minimum Version | Installation |
|------|----------------|--------------|
| **Docker** | 24+ | https://docs.docker.com/get-docker/ |
| **Docker Compose** | 2.x (included with Docker Desktop) | Bundled with Docker Desktop |
| **Git** | 2.x | https://git-scm.com/ |
| **Make** | 3.x (pre-installed on macOS/Linux) | Pre-installed on macOS; `apt install make` on Ubuntu |
| **Node.js** (optional, for local frontend dev) | 20.x | https://nodejs.org/ |
| **Python** (optional, for local backend dev) | 3.11+ | https://www.python.org/ |

> **Note:** Node.js and Python are only needed if you want to run services outside Docker for faster iteration. Docker handles all dependencies automatically.

---

## 2. Quick Start (Docker — Recommended)

### 2.1 Clone the Repository

```bash
git clone <repository-url>
cd AS2
```

### 2.2 Create the Environment File

```bash
cp .env.example .env
```

Open `.env` and configure the following required values:

| Variable | Action Required |
|----------|----------------|
| `OPENAI_API_KEY` | Replace with your real OpenAI API key |
| `DEEPSEEK_API_KEY` | Replace with your DeepSeek API key (or leave as placeholder if not using) |

All other variables have sensible development defaults and can be left as-is.

### 2.3 Start All Services

```bash
make dev-build
```

This single command will:
1. Build Docker images for the frontend and backend.
2. Pull images for PostgreSQL, Redis, ChromaDB, and MinIO.
3. Start all 6 containers on a shared Docker network.
4. Apply volume mounts for hot-reload (code changes reflect immediately).

### 2.4 Verify Everything Is Running

| Service | URL | Expected Result |
|---------|-----|-----------------|
| **Frontend** | http://localhost:3000 | JobFit AI landing page |
| **Backend API** | http://localhost:8000/api/health | `{"status": "ok", "service": "jobfit-ai-backend"}` |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **MinIO Console** | http://localhost:9001 | MinIO dashboard (login: minioadmin / minioadmin) |
| **PostgreSQL** | localhost:5432 | Connect via any DB client (user: postgres, pass: postgres, db: jobfit_dev) |
| **Redis** | localhost:6379 | Connect via `redis-cli` |
| **ChromaDB** | http://localhost:8200 | ChromaDB API |

### 2.5 Stop All Services

```bash
make down
```

---

## 3. Makefile Command Reference

All common operations are available via `make` commands. Run from the project root.

### Development

| Command | Description |
|---------|-------------|
| `make dev` | Start all services (uses cached images) |
| `make dev-build` | Start all services with a fresh image build |
| `make down` | Stop all services (data volumes preserved) |
| `make logs` | Tail logs from all containers |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run both backend and frontend tests |
| `make test-backend` | Run backend tests only (`pytest -v`) |
| `make test-frontend` | Run frontend tests only (`npm test`) |
| `make lint` | Run all linters and type checks (Ruff, mypy, ESLint, tsc) |

### Database

| Command | Description |
|---------|-------------|
| `make migrate` | Apply all pending Alembic migrations |
| `make migrate-create msg="add users table"` | Generate a new migration from model changes |
| `make seed` | Populate the database with development test data |

### Cleanup

| Command | Description |
|---------|-------------|
| `make clean` | Stop all services AND delete all volumes and local images (full reset) |

---

## 4. Local Development (Without Docker)

For faster iteration, you can run the backend or frontend directly on your machine while keeping data services (PostgreSQL, Redis, etc.) in Docker.

### 4.1 Start Data Services Only

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up postgres redis chromadb minio
```

### 4.2 Run Backend Locally

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables (adjust DB host from 'postgres' to 'localhost')
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/jobfit_dev"
export REDIS_URL="redis://localhost:6379/0"
export CHROMA_HOST="localhost"
export S3_ENDPOINT="http://localhost:9000"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.3 Run Frontend Locally

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The frontend will be available at http://localhost:3000 with hot module replacement.

---

## 5. Database Operations

### 5.1 First-Time Setup

After starting the services for the first time, initialize the database schema:

```bash
make migrate
```

### 5.2 Creating a New Migration

When you modify SQLAlchemy ORM models, generate a migration:

```bash
make migrate-create msg="describe your change here"
```

This creates a new file in `backend/alembic/versions/`. Review it before applying.

### 5.3 Applying Migrations

```bash
make migrate
```

### 5.4 Rolling Back

```bash
# Roll back the last migration
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend alembic downgrade -1

# Roll back to a specific revision
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend alembic downgrade <revision_id>
```

### 5.5 Connecting to the Database

```bash
# Via Docker
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U postgres -d jobfit_dev

# Or use any GUI tool (DBeaver, pgAdmin, TablePlus) with:
# Host: localhost, Port: 5432, User: postgres, Password: postgres, Database: jobfit_dev
```

---

## 6. Running Tests

### 6.1 Backend Tests

```bash
# All backend tests
make test-backend

# Run a specific test file
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pytest tests/test_optimization.py -v

# Run tests with coverage report
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pytest --cov=. --cov-report=term-missing

# Run only tenant isolation tests
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pytest -m tenant_isolation -v
```

### 6.2 Frontend Tests

```bash
# All frontend tests
make test-frontend

# Run with coverage
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm run test:coverage
```

### 6.3 Linting and Type Checking

```bash
make lint
```

This runs all four quality checks:
1. `ruff check .` — Python linting
2. `mypy --strict .` — Python type checking
3. `eslint src/` — TypeScript/JavaScript linting
4. `tsc --noEmit` — TypeScript type checking

---

## 7. Project Structure Overview

```
AS2/
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # Application entry point
│   ├── config.py               # Settings (pydantic-settings)
│   ├── shared/                 # Shared kernel (base classes, middleware)
│   ├── identity/               # Auth & tenant management [Person B]
│   ├── resume/                 # Resume upload & parsing [Person B]
│   ├── optimization/           # AI optimization pipeline [Person A]
│   ├── interview/              # Interview prep & cover letter [Person A]
│   ├── billing/                # Subscription & quotas [Person B]
│   └── tests/                  # Test suite
├── frontend/                   # Next.js React frontend [Person B]
│   └── src/
│       ├── app/                # Pages (App Router)
│       ├── components/         # UI components
│       ├── containers/         # Data-fetching containers
│       ├── hooks/              # Custom React hooks
│       ├── providers/          # Context providers
│       ├── lib/                # Utilities & API client
│       └── types/              # TypeScript type definitions
├── docs/                       # Project documentation
├── docker-compose.yml          # Base service definitions
├── docker-compose.dev.yml      # Development overrides
├── docker-compose.prod.yml     # Production overrides
├── Makefile                    # Command shortcuts
├── .env.example                # Environment variable template
└── .gitignore                  # Git ignore rules
```

### Team Ownership

| Area | Owner | Description |
|------|-------|-------------|
| `optimization/` + `interview/` | **Person A** (AI Workflow) | LangGraph agents, RAG pipeline, ATS scoring, interview Q&A generation |
| Everything else | **Person B** (Platform) | Auth, resume parsing, billing, frontend, Docker, CI/CD |
| `shared/` + `config.py` | **Both** | Shared kernel — coordinate changes here |

---

## 8. Common Issues and Troubleshooting

### Port Already in Use

```
Error: bind: address already in use
```

**Fix:** Another service is using the port. Find and stop it:

```bash
# Find process using port 3000 (or 8000, 5432, etc.)
lsof -i :3000
# Kill it
kill -9 <PID>
```

### Docker Build Fails with "No Space Left on Device"

**Fix:** Clean up unused Docker resources:

```bash
docker system prune -a --volumes
```

### Backend Cannot Connect to PostgreSQL

Ensure PostgreSQL is healthy before the backend starts. Check container status:

```bash
docker compose ps
```

If PostgreSQL shows "unhealthy", check its logs:

```bash
docker compose logs postgres
```

### Frontend Shows Blank Page

Clear the Next.js cache and rebuild:

```bash
make down
docker volume rm $(docker volume ls -q | grep jobfit)
make dev-build
```

### "Module Not Found" Errors in Backend

If running locally (not in Docker), ensure your virtual environment is activated and dependencies are installed:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Hot Reload Not Working

- **Backend:** Ensure `uvicorn --reload` is running (default in dev). Check that `./backend:/app` volume mount is present in `docker-compose.dev.yml`.
- **Frontend:** Ensure `./frontend:/app` volume mount is present. If changes still don't reflect, restart the container: `docker compose restart frontend`.

---

## 9. Production Deployment

### 9.1 Prepare the Server (AWS EC2)

```bash
# Install Docker on Ubuntu
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### 9.2 Deploy

```bash
# Clone the repository on the server
git clone <repository-url>
cd AS2

# Create production .env (fill in real secrets)
cp .env.example .env
nano .env    # Edit with production values
chmod 600 .env

# Build and start in production mode
make prod-build
```

### 9.3 Production .env Checklist

Before deploying, ensure these variables are updated in `.env`:

| Variable | Production Value |
|----------|-----------------|
| `APP_ENV` | `production` |
| `DATABASE_URL` | Strong password, `jobfit_prod` database |
| `JWT_SECRET_KEY` | Random 64-character string |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `OPENAI_API_KEY` | Production API key |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | Strong credentials |
| `LOG_LEVEL` | `WARNING` |
| `UVICORN_WORKERS` | `4` (or `2 * CPU + 1`) |
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com` |

### 9.4 Verify Production Deployment

```bash
curl http://your-server-ip:8000/api/health
# Expected: {"status":"ok","service":"jobfit-ai-backend"}
```

### 9.5 View Production Logs

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```
