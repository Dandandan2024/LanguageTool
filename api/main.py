from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, date
import os, json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from placement_cat import PlacementCAT

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

class PlacementStartRequest(BaseModel):
    username: str
    language: str = "ru"
    claimed_level: str | None = None

class PlacementAnswerRequest(BaseModel):
    session_id: str
    card_id: str
    user_answer: str
    response_time_ms: int | None = None

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

@app.options("/v1/placement/start")
def placement_start_options():
    return {"message": "OK"}

@app.options("/v1/placement/answer")
def placement_answer_options():
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
                SELECT DATE(ts) as date, COUNT(*) as count
                FROM review_log 
                WHERE user_id = %s 
                AND ts >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(ts)
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

# Initialize CAT system
cat_system = PlacementCAT()

@app.post("/v1/placement/start")
def start_placement_test(request: PlacementStartRequest):
    """Start a new adaptive placement test"""
    try:
        conn = db()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Create new placement session
            session_data = cat_system.start_session(request.claimed_level)
            
            cur.execute("""
                INSERT INTO placement_sessions (user_id, language, current_theta, theta_se, items_completed)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (request.username, request.language, session_data['theta'], 
                  session_data['se'], session_data['items_completed']))
            
            session_id = cur.fetchone()['id']
            
            # Get Russian cards for placement (all types with theta values)
            cur.execute("""
                SELECT id, type, payload FROM cards 
                WHERE language = 'ru' AND payload ? 'theta'
                ORDER BY RANDOM()
                LIMIT 50
            """, ())
            
            available_items = []
            for row in cur.fetchall():
                payload = row['payload']
                if isinstance(payload, str):
                    payload = json.loads(payload)
                available_items.append({
                    'id': row['id'],
                    'type': row['type'],
                    'theta': payload.get('theta', 0.0),
                    **payload
                })
            
            if not available_items:
                raise HTTPException(status_code=404, detail="No placement items available")
            
            # Select best first item
            selected_item = cat_system.select_next_item(session_data['theta'], available_items)
            
            if not selected_item:
                raise HTTPException(status_code=404, detail="No suitable item found")
            
            # Format item to match frontend expectations (type, payload structure)
            formatted_item = {
                "id": selected_item['id'],
                "type": selected_item['type'],
                "payload": {k: v for k, v in selected_item.items() if k not in ['id', 'type']}
            }
            
            return {
                "session_id": session_id,
                "item": formatted_item,
                "progress": {
                    "items_completed": 0,
                    "estimated_level": cat_system.get_final_cefr(session_data['theta']),
                    "confidence_interval": cat_system.get_confidence_interval(session_data['theta'], session_data['se'])
                }
            }
            
    except Exception as e:
        print(f"Placement start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.post("/v1/placement/answer")
def submit_placement_answer(request: PlacementAnswerRequest):
    """Submit answer and get next placement item"""
    try:
        conn = db()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get current session
            cur.execute("""
                SELECT * FROM placement_sessions WHERE id = %s
            """, (request.session_id,))
            
            session = cur.fetchone()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if session['is_complete']:
                raise HTTPException(status_code=400, detail="Session already complete")
            
            # Get the item that was answered
            cur.execute("""
                SELECT type, payload FROM cards WHERE id = %s
            """, (request.card_id,))
            
            card_row = cur.fetchone()
            if not card_row:
                raise HTTPException(status_code=404, detail="Card not found")
                
            card_payload = card_row['payload']
            if isinstance(card_payload, str):
                card_payload = json.loads(card_payload)
            
            # Check if answer is correct based on card type
            card_type = card_row.get('type', 'unknown')
            is_correct = False
            correct_answer = ""
            
            if card_type == 'cloze':
                correct_answer = card_payload.get('answer', '').lower()
                user_answer = request.user_answer.lower()
                is_correct = user_answer == correct_answer
            elif card_type == 'vocabulary':
                # For vocabulary, check if translation is correct
                correct_answer = card_payload.get('translation', '').lower()
                user_answer = request.user_answer.lower()
                is_correct = user_answer == correct_answer
            elif card_type == 'sentence':
                # For sentence, check if English translation is correct
                correct_answer = card_payload.get('english', '').lower()
                user_answer = request.user_answer.lower()
                is_correct = user_answer == correct_answer
            else:
                # Fallback for unknown types
                correct_answer = card_payload.get('answer', card_payload.get('translation', card_payload.get('english', ''))).lower()
                user_answer = request.user_answer.lower()
                is_correct = user_answer == correct_answer
            
            # Update ability estimate
            item_theta = card_payload.get('theta', 0.0)
            new_theta, new_se = cat_system.update_ability(
                session['current_theta'], 
                session['theta_se'], 
                item_theta, 
                is_correct
            )
            
            # Record response
            cur.execute("""
                INSERT INTO placement_responses 
                (session_id, card_id, user_response, correct_answer, is_correct, 
                 response_time_ms, theta_before, theta_after, se_before, se_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (request.session_id, request.card_id, request.user_answer, 
                  correct_answer, is_correct, request.response_time_ms,
                  session['current_theta'], new_theta, session['theta_se'], new_se))
            
            # Update session
            items_completed = session['items_completed'] + 1
            should_stop = cat_system.should_stop(new_se, items_completed)
            
            if should_stop:
                # Complete the session
                final_cefr = cat_system.get_final_cefr(new_theta)
                known_words = cat_system.generate_known_words(final_cefr, session['language'])
                
                cur.execute("""
                    UPDATE placement_sessions 
                    SET current_theta = %s, theta_se = %s, items_completed = %s,
                        is_complete = TRUE, final_cefr = %s, final_theta = %s,
                        updated_at = now()
                    WHERE id = %s
                """, (new_theta, new_se, items_completed, final_cefr, new_theta, request.session_id))
                
                return {
                    "complete": True,
                    "results": {
                        "cefr_level": final_cefr,
                        "theta": new_theta,
                        "confidence_interval": cat_system.get_confidence_interval(new_theta, new_se),
                        "items_completed": items_completed,
                        "known_words": known_words[:50]  # First 50 words
                    }
                }
            else:
                # Get next item
                cur.execute("""
                    SELECT id FROM placement_responses WHERE session_id = %s
                """, (request.session_id,))
                used_items = [row['id'] for row in cur.fetchall()]
                
                cur.execute("""
                    SELECT id, type, payload FROM cards 
                    WHERE language = 'ru' AND payload ? 'theta' AND id NOT IN %s
                    ORDER BY RANDOM()
                    LIMIT 20
                """, (tuple(used_items) if used_items else ('',),))
                
                available_items = []
                for row in cur.fetchall():
                    payload = row['payload']
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    available_items.append({
                        'id': row['id'],
                        'type': row['type'],
                        'theta': payload.get('theta', 0.0),
                        **payload
                    })
                
                if not available_items:
                    # Force completion if no more items
                    final_cefr = cat_system.get_final_cefr(new_theta)
                    cur.execute("""
                        UPDATE placement_sessions 
                        SET is_complete = TRUE, final_cefr = %s, final_theta = %s
                        WHERE id = %s
                    """, (final_cefr, new_theta, request.session_id))
                    
                    return {"complete": True, "results": {"cefr_level": final_cefr}}
                
                # Select next best item
                selected_item = cat_system.select_next_item(new_theta, available_items)
                
                if not selected_item:
                    # Force completion if no suitable item found
                    final_cefr = cat_system.get_final_cefr(new_theta)
                    cur.execute("""
                        UPDATE placement_sessions 
                        SET is_complete = TRUE, final_cefr = %s, final_theta = %s
                        WHERE id = %s
                    """, (final_cefr, new_theta, request.session_id))
                    
                    return {"complete": True, "results": {"cefr_level": final_cefr}}
                
                # Format item to match frontend expectations (type, payload structure)
                formatted_item = {
                    "id": selected_item['id'],
                    "type": selected_item['type'],
                    "payload": {k: v for k, v in selected_item.items() if k not in ['id', 'type']}
                }
                
                # Update session
                cur.execute("""
                    UPDATE placement_sessions 
                    SET current_theta = %s, theta_se = %s, items_completed = %s, updated_at = now()
                    WHERE id = %s
                """, (new_theta, new_se, items_completed, request.session_id))
                
                return {
                    "complete": False,
                    "item": formatted_item,
                    "feedback": {
                        "was_correct": is_correct,
                        "correct_answer": correct_answer
                    },
                    "progress": {
                        "items_completed": items_completed,
                        "estimated_level": cat_system.get_final_cefr(new_theta),
                        "confidence_interval": cat_system.get_confidence_interval(new_theta, new_se)
                    }
                }
                
    except Exception as e:
        print(f"Placement answer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
