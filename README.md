# LangTool MVP with Scheduler

## Backend Endpoints
- `POST /encounter` — log a phrase encounter
- `POST /grade` — update review state (SM-2)
- `GET /due` — list due phrases for review

Sample test:
```bash
curl -X POST http://localhost:5000/encounter   -H "Content-Type: application/json"   -d '{"user_id":1,"phrase_id":101,"signals":["tap"],"raw_text":"bonjour"}'

curl -X POST http://localhost:5000/grade   -H "Content-Type: application/json"   -d '{"user_id":1,"phrase_id":101,"grade":4}'

curl "http://localhost:5000/due?user_id=1&limit=5"
```
