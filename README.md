# LangTool MVP

This repository contains the MVP implementation for the Adaptive Conversation + Live Recycling language learning tool.

## Structure
- `/frontend` — React + Vite app
- `/backend` — Express + PostgreSQL API
- `/docs` — Project docs
- `/scripts` — Utility scripts

## Setup
1. Install dependencies in each folder:
```bash
cd backend && npm install
cd ../frontend && npm install
```

2. Run backend:
```bash
cd backend
cp .env.example .env
npm run dev
```

3. Run frontend:
```bash
cd frontend
npm run dev
```
