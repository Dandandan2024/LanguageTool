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
    "https://language-tool-seven.vercel.app",
    "https://language-tool-5ldlf5vxv-daniels-projects-a9d5dc59.vercel.app",
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
    username: str = "anonymous"

@app.post("/v1/sessions/next")
def sessions_next(req: NextRequest):
    # Fetch due cards + some new ones
    conn = db()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get cards - simplified query to avoid database errors
            cur.execute("""
                SELECT c.id as card_id, c.type, c.payload, NULL as due_date, NULL as interval_days
                FROM cards c
                ORDER BY RANDOM()
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
    username: str = "anonymous"

@app.post("/v1/reviews")
def submit_reviews(items: list[ReviewItem]):
    try:
        conn = db()
        with conn, conn.cursor() as cur:
            for item in items:
                # For demo purposes, use default values for stability/difficulty
                # In a real app, you'd load these from user_cards
                stability = 3.0
                difficulty = 0.3
                stability, difficulty, next_days = fsrs_update(stability, difficulty, item.rating)
                due_date = date.today() + timedelta(days=next_days)
                
                # Simplified: Just record the review (ignore user_cards for now)
                try:
                    cur.execute("""
                        INSERT INTO review_log(user_id, card_id, rating, response_time_ms) 
                        VALUES (%s, %s, %s, %s)
                    """, (item.username, item.card_id, item.rating, item.response_time_ms or 0))
                except Exception as e:
                    print(f"Database error: {e}")
                    # Continue with other items even if one fails
                    continue
            
            conn.commit()
            return {"updated": len(items)}
    except Exception as e:
        print(f"Review submission error: {e}")
        return {"error": str(e), "updated": 0}
    finally:
        if 'conn' in locals():
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

@app.options("/v1/stats/{username}")
def stats_options(username: str):
    return {"message": "OK"}

@app.get("/v1/stats/{username}")
def get_user_stats(username: str):
    """Get comprehensive statistics for a user"""
    conn = db()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total reviews
            cur.execute("""
                SELECT COUNT(*) as total_reviews
                FROM review_log 
                WHERE user_id = %s
            """, (username,))
            total_reviews = cur.fetchone()['total_reviews'] or 0
            
            # Reviews by rating (accuracy)
            cur.execute("""
                SELECT rating, COUNT(*) as count
                FROM review_log 
                WHERE user_id = %s
                GROUP BY rating
                ORDER BY rating
            """, (username,))
            ratings_breakdown = cur.fetchall()
            
            # Daily activity (last 30 days)
            cur.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM review_log 
                WHERE user_id = %s 
                AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (username,))
            daily_activity = cur.fetchall()
            
            # Language breakdown
            cur.execute("""
                SELECT c.language, COUNT(*) as reviews
                FROM review_log r
                JOIN cards c ON r.card_id = c.id
                WHERE r.user_id = %s
                GROUP BY c.language
            """, (username,))
            language_breakdown = cur.fetchall()
            
            # Calculate accuracy
            good_reviews = sum(r['count'] for r in ratings_breakdown if r['rating'] >= 3)
            accuracy = (good_reviews / total_reviews * 100) if total_reviews > 0 else 0
            
            # Study streak (simplified - days with reviews)
            study_streak = len(daily_activity)
            
            return {
                "username": username,
                "total_reviews": total_reviews,
                "accuracy_percentage": round(accuracy, 1),
                "study_streak_days": study_streak,
                "ratings_breakdown": ratings_breakdown,
                "daily_activity": daily_activity,
                "language_breakdown": language_breakdown
            }
            
    except Exception as e:
        print(f"Stats error: {e}")
        return {
            "username": username,
            "total_reviews": 0,
            "accuracy_percentage": 0,
            "study_streak_days": 0,
            "ratings_breakdown": [],
            "daily_activity": [],
            "language_breakdown": []
        }
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
