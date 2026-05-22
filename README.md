# Docker 3-Tier Task Manager

A production-pattern 3-tier web application running entirely in Docker Compose.
Demonstrates container networking, health checks, named volumes, environment variable
injection, and reverse proxy routing — all core DevOps skills.

![Architecture](https://img.shields.io/badge/Tier%201-Nginx-009639?style=flat)
![Architecture](https://img.shields.io/badge/Tier%202-Flask%20API-3C3489?style=flat)
![Architecture](https://img.shields.io/badge/Tier%203-PostgreSQL-336791?style=flat)

---

## Architecture

```
Browser
   |
   | :8080
   v
+------------------+
|   Nginx           |  Tier 1 — Reverse Proxy
|   (port 80)       |  Routes / to frontend, /api/* to Flask
+------------------+
   |            |
   v            v
+----------+ +----------+
| Frontend | | Flask API |  Tier 2 — Application Layer
| (nginx)  | | (port 5000)|
+----------+ +----------+
                  |
                  v
           +------------+
           | PostgreSQL  |  Tier 3 — Data Layer
           | (port 5432) |  Data persists in named volume
           +------------+
```

## Why 3 tiers?

| Tier | Container | Responsibility |
|------|-----------|----------------|
| 1 | Nginx | Single entry point. Terminates HTTP. Routes traffic. Hides internal ports. |
| 2 | Flask API | Business logic. CRUD operations. DB connection management with retry logic. |
| 2 | Frontend | Static HTML/JS. Talks to API via relative URLs (goes through Nginx). |
| 3 | PostgreSQL | Persistent data. Named volume survives container restarts. |

## Key Concepts Demonstrated

**depends_on with health checks** — API waits for PostgreSQL to be healthy before starting.
PostgreSQL healthcheck uses `pg_isready`. API healthcheck hits `/health` endpoint.
Without this: API starts, tries to connect to DB, fails immediately.

**Named volumes** — `postgres_data` volume is NOT deleted on `docker-compose down`.
Only deleted with `docker-compose down -v`. This is how you persist database data in Docker.

**Environment variable injection** — sensitive values (DB password) come from `.env` file.
`.env` is in `.gitignore` — never committed to Git. `.env.example` is committed instead.

**Docker network** — all containers share `app_network`. They reach each other by
service name (`postgres`, `api`, `frontend`) not by IP address.
Only port 8080 is exposed to your laptop. Everything else is internal.

**Non-root containers** — API runs as `appuser` not `root`. Security best practice.

**Retry logic** — `get_db()` retries 5 times with 3s delay. Handles the race condition
where the API container starts before PostgreSQL is fully ready.

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/viswa-tej/docker-3tier-app
cd docker-3tier-app

# 2. Create your .env file (copy the example)
cp .env.example .env
# Edit .env and change POSTGRES_PASSWORD to something strong

# 3. Start everything
make up

# 4. Open the app
# Go to http://localhost:8080 in your browser
```

## All Commands

```bash
make up        # Build images and start all 4 containers
make down      # Stop containers (data is kept)
make logs      # Tail logs from all containers
make logs-api  # Tail API logs only
make ps        # Show container status and health
make health    # Check API health endpoint
make clean     # Stop everything AND delete all data
make restart   # Restart all services
```

## Verify It's Working

```bash
# Check all containers are healthy
make ps
# Expected: all 4 containers showing "healthy" or "running"

# Test the API directly
curl http://localhost:8080/health
# Expected: {"service": "api", "status": "healthy"}

curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "My first task"}'
# Expected: {"done": false, "id": 1, "title": "My first task"}

curl http://localhost:8080/api/tasks
# Expected: array containing your task

# Verify data persists across restarts
make down && make up
curl http://localhost:8080/api/tasks
# Task is still there — named volume preserved the data
```

## File Structure

```
docker-3tier-app/
├── docker-compose.yml     # Orchestrates all 4 services
├── .env.example           # Template for environment variables
├── .env                   # Your actual values (gitignored)
├── Makefile               # Developer shortcuts
├── nginx/
│   └── nginx.conf         # Reverse proxy routing rules
├── api/
│   ├── app.py             # Flask REST API (CRUD for tasks)
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Non-root, gunicorn, healthcheck
└── frontend/
    ├── index.html         # Single-page app (vanilla JS)
    └── Dockerfile         # Nginx serving static files
```

## What I learned

- Docker Compose service dependency ordering with `condition: service_healthy`
- Named volumes vs bind mounts — when to use each
- Nginx as a reverse proxy — routing rules and upstream configuration
- Environment variable injection via `.env` files — keeping secrets out of Git
- Container health checks — Docker-native vs Kubernetes-style probes
- Network isolation — only exposing what needs to be public
- Retry logic for dependent services — handling startup race conditions
