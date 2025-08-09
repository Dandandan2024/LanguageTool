from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, date
import os, json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Adaptive SRS API", version="0.1.0")

# Add CORS middleware
# Allow both local development and production origins
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Production Vercel domains (both old and new)
    "https://language-tool-hs6owowje-daniels-projects-a9d5dc59.vercel.app",
    "https://language-tool-o5tyo0qa9-daniels-projects-a9d5dc59.vercel.app",
    # Allow all vercel.app subdomains as backup
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

def db():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    return conn

# --- FSRS stub (replace with real formulas) ---
def fsrs_update(stability: float, difficulty: float, rating: int):
    # Very rough placeholder just to wire the flow
    if rating == 1:  # Again
        stability = max(1.0, stability * 0.5)
        difficulty = min(0.9, difficulty + 0.05)
    elif rating == 2:  # Hard
        stability = max(1.5, stability * 0.9)
        difficulty = min(0.85, difficulty + 0.02)
    elif rating == 3:  # Good
        stability = max(2.0, stability * 1.2)
        difficulty = max(0.15, difficulty - 0.01)
    else:  # Easy
        stability = max(3.0, stability * 1.4)
        difficulty = max(0.1, difficulty - 0.02)
    # Next interval heuristic
    next_days = max(1, int(stability))
    return stability, difficulty, next_days

class NextRequest(BaseModel):
    count: int = 20

@app.post("/v1/sessions/next")
def sessions_next(req: NextRequest):
    # Fetch due cards + some new ones
    conn = db()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get cards, joining with user_cards if they exist
            cur.execute("""
                SELECT c.id as card_id, c.type, c.payload, uc.due_date
                FROM cards c
                LEFT JOIN user_cards uc ON uc.card_id = c.id
                LIMIT %s
            """, (req.count,))
            rows = cur.fetchall()
            return {"items": rows}
    finally:
        conn.close()

class ReviewItem(BaseModel):
    card_id: str
    rating: int
    response_time_ms: int | None = None

@app.post("/v1/reviews")
def submit_reviews(items: list[ReviewItem]):
    conn = db()
    try:
        with conn, conn.cursor() as cur:
            for item in items:
                # For demo purposes, use default values for stability/difficulty
                # In a real app, you'd load these from user_cards
                stability = 3.0
                difficulty = 0.3
                stability, difficulty, next_days = fsrs_update(stability, difficulty, item.rating)
                due_date = date.today() + timedelta(days=next_days)
                
                # Record review in review_log
                cur.execute("""
                    INSERT INTO review_log(user_id, card_id, rating, response_time_ms) 
                    VALUES (gen_random_uuid(), %s, %s, %s)
                """, (item.card_id, item.rating, item.response_time_ms))
            
            return {"updated": len(items)}
    finally:
        conn.close()

@app.get("/")
def root():
    return {"message": "Adaptive SRS API is running!", "status": "healthy"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.options("/v1/sessions/next")
def sessions_next_options():
    return {"message": "OK"}

@app.options("/v1/reviews")
def reviews_options():
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
