# Adaptive SRS — Monorepo (Starter)

This is a minimal starter to get you moving. It includes:
- `apps/api` — FastAPI skeleton with review endpoints and FSRS hooks
- `apps/web` — Next.js (placeholder) with a one-screen review UI scaffold
- `packages/fsrs_py` — FSRS v4 stub (Python); mirror to TS later for offline
- `infra/` — docker-compose for Postgres + Redis; .env.example for config

## Quick start

### 1) Prereqs
- Python 3.11+
- Node 20+
- Docker + Docker Compose

### 2) Configure environment
Copy `.env.example` to `.env` and adjust values if needed.
```bash
cp .env.example .env
```

### 3) Start infra (Postgres + Redis)
```bash
docker compose -f infra/docker-compose.yml up -d
```

### 4) API (FastAPI)
```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Create tables
python scripts/init_db.py
# Run dev server
uvicorn main:app --reload --port 8000
```

### 5) Web (Next.js)
```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 for the web app and http://localhost:8000/docs for the API docs.

## Notes
- The FSRS implementation here is a minimal stub; replace with the reference formulas.
- DB schema is a trimmed MVP subset; expand to match the full spec.
