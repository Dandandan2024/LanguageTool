# LangTool MVP with Frontend UI

## How to run
1. Backend:
```bash
cd backend
npm install
cp .env.example .env
npm run dev
```
2. Frontend:
```bash
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 (Vite default) to use the UI.

## UI Functions
- Log Encounter: Calls POST /encounter
- Send Grade: Calls POST /grade
- Get Due Items: Calls GET /due
