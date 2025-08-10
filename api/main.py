from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, date
import os, json
import uuid
import asyncio
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from services.placement_cat import PlacementCAT

# Import LLM content generation
from llm.generation_api import (
    GenerateContentRequest, GeneratedContentResponse,
    BatchGenerateRequest, BatchGenerateResponse,
    generate_single_content, generate_batch_content,
    get_generation_suggestions
)

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
    "https://language-tool-2771lyetk-daniels-projects-a9d5dc59.vercel.app",  # Current Vercel URL
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

# Redis client for ephemeral session items
def redis_client() -> redis.Redis:
    url = os.getenv("REDIS_URL")
    if url:
        return redis.Redis.from_url(url, decode_responses=True)
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return redis.Redis(host=host, port=port, decode_responses=True)

SESSION_TTL_SECONDS = int(os.getenv("SESSION_ITEM_TTL_SECONDS", "3600"))

def save_ephemeral_item(r: redis.Redis, item_id: str, payload: dict) -> None:
    r.hset(f"session:{item_id}", mapping={k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in payload.items()})
    r.expire(f"session:{item_id}", SESSION_TTL_SECONDS)

def get_ephemeral_item(r: redis.Redis, item_id: str) -> dict | None:
    data = r.hgetall(f"session:{item_id}")
    if not data:
        return None
    result: dict = {}
    for k, v in data.items():
        try:
            result[k] = json.loads(v)
        except Exception:
            result[k] = v
    return result

def delete_ephemeral_item(r: redis.Redis, item_id: str) -> None:
    r.delete(f"session:{item_id}")

# Import FSRS v4 implementation
from models.fsrs import FSRS, Card, Rating, State, schedule_card

# Initialize FSRS scheduler
fsrs_scheduler = FSRS()

def generate_cards_from_lexemes_for_user(cur, username, user_cefr, count, theta_min, theta_max):
    """Generate cards on-demand from lexemes for a specific user"""
    import json
    from random import choice
    
    # Map CEFR to theta for consistency
    cefr_theta_map = {"A1": -2.0, "A2": -1.0, "B1": 0.0, "B2": 1.0, "C1": 2.0, "C2": 3.0}
    target_theta = cefr_theta_map.get(user_cefr, 0.0)
    
    generated_cards = []
    
    try:
        # Find lexemes the user hasn't learned yet, prioritizing by frequency
        cur.execute("""
            SELECT l.id, l.lemma, l.pos, l.cefr_level, l.frequency_rank
            FROM lexemes l
            LEFT JOIN cards c ON l.id = c.lexeme_id
            LEFT JOIN user_cards uc ON c.id::text = uc.card_id AND uc.user_id = %s
            WHERE l.language = 'ru'
            AND l.cefr_level = %s
            AND (uc.card_id IS NULL OR uc.reps < 2)  -- New or barely learned
            ORDER BY COALESCE(l.frequency_rank, 999999) ASC
            LIMIT %s
        """, (username, user_cefr, count * 2))  # Get more than needed to have options
        
        available_lexemes = cur.fetchall()
        
        if not available_lexemes:
            # Fallback: get any lexemes in the theta range
            cur.execute("""
                SELECT l.id, l.lemma, l.pos, l.cefr_level, l.frequency_rank
                FROM lexemes l
                WHERE l.language = 'ru'
                ORDER BY COALESCE(l.frequency_rank, 999999) ASC
                LIMIT %s
            """, (count * 2,))
            available_lexemes = cur.fetchall()
        
        # Generate cards for selected lexemes
        for i, lexeme in enumerate(available_lexemes[:count]):
            if i >= count:
                break
                
            lexeme_id = lexeme['id']
            lemma = lexeme['lemma']
            pos = lexeme['pos'] or 'word'
            cefr = lexeme['cefr_level'] or user_cefr
            
            # Choose card type (vocabulary is simpler to generate)
            card_type = choice(['vocabulary', 'cloze'])
            
            # Create simple card payload
            if card_type == 'vocabulary':
                payload = {
                    "word": lemma,
                    "translation": f"[{pos}] What does '{lemma}' mean?",
                    "pos": pos,
                    "target_word": lemma,
                    "theta": target_theta,
                    "cefr_level": cefr,
                    "generation_method": "on_demand_simple",
                    "difficulty": cefr
                }
            else:  # cloze
                if pos == 'v':  # verb
                    text = f"Я хочу ___ это."
                    translation = "I want to ___ this."
                elif pos == 'noun':
                    text = f"Это мой ___."
                    translation = "This is my ___."
                else:
                    text = f"___ очень важно."
                    translation = "___ is very important."
                
                payload = {
                    "text": text,
                    "answer": lemma,
                    "translation": translation,
                    "target_word": lemma,
                    "theta": target_theta,
                    "cefr_level": cefr,
                    "generation_method": "on_demand_simple",
                    "hints": [f"{pos}"]
                }
            
            # Insert the generated card
            cur.execute("""
                INSERT INTO cards (type, language, payload, lexeme_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, type, payload
            """, (card_type, 'ru', json.dumps(payload, ensure_ascii=False), lexeme_id))
            
            new_card = cur.fetchone()
            
            # Format for session response
            generated_cards.append({
                'card_id': new_card['id'],
                'type': new_card['type'],
                'payload': new_card['payload'],
                'due_date': None,
                'interval_days': None,
                'stability': None,
                'difficulty': None,
                'reps': None,
                'lapses': None,
                'state': None
            })
            
    except Exception as e:
        print(f"Error generating cards from lexemes: {e}")
    
    return generated_cards

class NextRequest(BaseModel):
    count: int = 20
    username: str = "anonymous"

@app.post("/v1/sessions/next")
async def sessions_next(req: NextRequest):
    """Fetch lexeme-based session items; generate sentences on demand and cache ephemerally."""
    conn = db()
    r = redis_client()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user's CEFR level
            cur.execute("SELECT cefr_level, theta_estimate FROM simple_users WHERE username = %s", (req.username,))
            up = cur.fetchone()
            user_cefr = up['cefr_level'] if up else 'B1'

            # Collect due lexemes first
            today = date.today()
            cur.execute(
                """
                SELECT ul.lexeme_id, ul.state, ul.due_date, ul.stability, ul.difficulty, l.lemma, l.cefr_level
                FROM user_lexemes ul
                JOIN lexemes l ON l.id = ul.lexeme_id
                WHERE ul.user_id = %s AND (ul.due_date IS NULL OR ul.due_date <= %s)
                ORDER BY COALESCE(ul.due_date, %s) ASC
                LIMIT %s
                """,
                (req.username, today, today, req.count),
            )
            due_lexemes = cur.fetchall()

            remaining = req.count - len(due_lexemes)
            additional: list[dict] = []
            if remaining > 0:
                # Pick additional lexemes by CEFR and frequency that user hasn't seen
                cur.execute(
                    """
                    SELECT l.id as lexeme_id, 'new' as state, NULL as due_date, 0.0 as stability, 0.0 as difficulty,
                           l.lemma, l.cefr_level
                    FROM lexemes l
                    LEFT JOIN user_lexemes ul ON ul.lexeme_id = l.id AND ul.user_id = %s
                    WHERE ul.lexeme_id IS NULL AND l.language = 'ru' AND l.cefr_level = %s
                    ORDER BY COALESCE(l.frequency_rank, 999999)
                    LIMIT %s
                    """,
                    (req.username, user_cefr, remaining),
                )
                additional = cur.fetchall()
                # Initialize user_lexemes rows for these
                for row in additional:
                    cur.execute(
                        """
                        INSERT INTO user_lexemes (user_id, lexeme_id, state, due_date)
                        VALUES (%s, %s, 'new', %s)
                        ON CONFLICT (user_id, lexeme_id) DO NOTHING
                        """,
                        (req.username, row['lexeme_id'], today),
                    )

            selected = due_lexemes + additional

            # Generate ephemeral items
            from llm.content_generator import ContentGenerator, GenerationRequest, ContentType, CEFRLevel
            generator = ContentGenerator(conn)

            async def gen_item(row: dict) -> dict:
                lexeme_id = str(row['lexeme_id'])
                target_word = row['lemma']
                cefr = row['cefr_level'] or user_cefr
                req_obj = GenerationRequest(
                    target_word=target_word,
                    target_lexeme_id=lexeme_id,
                    content_type=ContentType.SENTENCE,
                    user_cefr=CEFRLevel(cefr),
                    user_id=req.username,
                )
                content = await generator.generate_content(req_obj)
                item_id = str(uuid.uuid4())
                payload = {
                    'session_item_id': item_id,
                    'user_id': req.username,
                    'lexeme_id': lexeme_id,
                    'content_type': content.content_type.value,
                    'question_text': content.question_text,
                    'answer_text': content.answer_text,
                    'target_word': content.target_word,
                    'difficulty_theta': content.difficulty_theta,
                    'supporting_words': content.supporting_words,
                    'metadata': content.metadata,
                    'created_at': datetime.now().isoformat(),
                }
                save_ephemeral_item(r, item_id, payload)
                return {
                    'session_item_id': item_id,
                    'type': 'sentence',
                    'payload': {
                        'question_text': content.question_text,
                        'cefr_level': cefr,
                        'supporting_words': content.supporting_words,
                        'answer_text': content.answer_text,
                    },
                }

            tasks = [gen_item(row) for row in selected[: req.count]]
            items = await asyncio.gather(*tasks)
            
            return {
                'items': items,
                'user_cefr': user_cefr,
                'count': len(items),
            }
    except Exception as e:
        print(f"Sessions next error: {e}")
        return {'items': [], 'user_cefr': 'B1', 'count': 0, 'error': str(e)}
    finally:
        conn.close()

class ReviewItem(BaseModel):
    session_item_id: str | None = None
    card_id: str | None = None  # backward-compat
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
    """Submit reviews for generated session items; update FSRS for lexemes and log the review."""
    try:
        conn = db()
        r = redis_client()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            updated_count = 0
            now = datetime.now()
            
            for item in items:
                try:
                    session_item_id = item.session_item_id
                    if not session_item_id and item.card_id:
                        # backward-compat not supported in lexeme mode
                        print(f"Skipping legacy card_id review: {item.card_id}")
                        continue
                    session_payload = get_ephemeral_item(r, session_item_id)
                    if not session_payload:
                        print(f"Session item expired or missing: {session_item_id}")
                        continue

                    lexeme_id = session_payload.get('lexeme_id')
                    # Load current FSRS-like state from user_lexemes
                    cur.execute(
                        """
                        SELECT * FROM user_lexemes WHERE user_id = %s AND lexeme_id = %s
                        """,
                        (item.username, uuid.UUID(lexeme_id)),
                    )
                    row = cur.fetchone()
                    if row:
                        state_name = (row['state'] or 'new').upper()
                        try:
                            state_enum = State[state_name]
                        except Exception:
                            state_enum = State.NEW
                        card = Card(
                            due=row['due_date'] or now.date(),
                            stability=row['stability'] or 0.0,
                            difficulty=row['difficulty'] or 0.0,
                            elapsed_days=row['elapsed_days'] or 0,
                            scheduled_days=row['scheduled_days'] or 0,
                            reps=row['reps'] or 0,
                            lapses=row['lapses'] or 0,
                            state=state_enum,
                            last_review=row['last_review'],
                        )
                    else:
                        card = fsrs_scheduler.init_card(now)
                    
                    rating = Rating(item.rating)
                    before = card
                    updated_card, review_log = schedule_card(card, rating, now)
                    
                    # Upsert user_lexemes with new state
                    cur.execute(
                        """
                        INSERT INTO user_lexemes (
                            user_id, lexeme_id, stability, difficulty, interval_days, due_date,
                            reps, lapses, last_review, state, scheduled_days, elapsed_days
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, lexeme_id)
                        DO UPDATE SET
                            stability = EXCLUDED.stability,
                            difficulty = EXCLUDED.difficulty,
                            interval_days = EXCLUDED.interval_days,
                            due_date = EXCLUDED.due_date,
                            reps = EXCLUDED.reps,
                            lapses = EXCLUDED.lapses,
                            last_review = EXCLUDED.last_review,
                            state = EXCLUDED.state,
                            scheduled_days = EXCLUDED.scheduled_days,
                            elapsed_days = EXCLUDED.elapsed_days
                        """,
                        (
                            item.username,
                            uuid.UUID(lexeme_id),
                            updated_card.stability,
                            updated_card.difficulty,
                            updated_card.scheduled_days,
                            updated_card.due.date(),
                            updated_card.reps,
                            updated_card.lapses,
                            updated_card.last_review,
                            updated_card.state.name.lower(),
                            updated_card.scheduled_days,
                            updated_card.elapsed_days,
                        ),
                    )

                    # Insert lexeme review log
                    cur.execute(
                        """
                        INSERT INTO lexeme_review_log (
                            user_id, lexeme_id, content_id, rating, response_time_ms, word_form_shown, content_type,
                            stability_before, stability_after, difficulty_before, difficulty_after, ts
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            item.username,
                            uuid.UUID(lexeme_id),
                            None,
                            item.rating,
                            item.response_time_ms or 0,
                            None,
                            session_payload.get('content_type', 'sentence'),
                            before.stability,
                            updated_card.stability,
                            before.difficulty,
                            updated_card.difficulty,
                            now,
                        ),
                    )

                    # Remove ephemeral item
                    delete_ephemeral_item(r, session_item_id)
                    updated_count += 1
                except Exception as e:
                    print(f"Error processing review for session {getattr(item,'session_item_id',None)}: {e}")
                    continue
            
            conn.commit()
            return {"updated": updated_count, "message": f"Updated {updated_count} lexemes"}
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

@app.options("/v1/user/{username}")
def user_profile_options(username: str):
    return {"message": "OK"}

@app.get("/v1/stats/{username}")
def get_user_stats(username: str):
    """Get comprehensive statistics for a user"""
    conn = db()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Total reviews (prefer lexeme_review_log)
            try:
                cur.execute("SELECT COUNT(*) as cnt FROM lexeme_review_log WHERE user_id = %s", (username,))
                total_reviews = cur.fetchone()['cnt'] or 0
            except Exception:
                cur.execute("SELECT COUNT(*) as cnt FROM review_log WHERE user_id = %s", (username,))
                total_reviews = cur.fetchone()['cnt'] or 0
            
            # Reviews by rating (accuracy)
            try:
                cur.execute(
                    "SELECT rating, COUNT(*) as count FROM lexeme_review_log WHERE user_id = %s GROUP BY rating ORDER BY rating",
                    (username,),
                )
                ratings_breakdown = cur.fetchall()
            except Exception:
                cur.execute(
                    "SELECT rating, COUNT(*) as count FROM review_log WHERE user_id = %s GROUP BY rating ORDER BY rating",
                    (username,),
                )
            ratings_breakdown = cur.fetchall()
            
            # Daily activity (last 30 days)
            try:
                cur.execute(
                    """
                    SELECT DATE(ts) as date, COUNT(*) as count
                    FROM lexeme_review_log 
                    WHERE user_id = %s 
                    AND ts >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(ts)
                    ORDER BY date DESC
                    """,
                    (username,),
                )
                daily_activity = cur.fetchall()
            except Exception:
                cur.execute(
                    """
                SELECT DATE(ts) as date, COUNT(*) as count
                FROM review_log 
                WHERE user_id = %s 
                AND ts >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(ts)
                ORDER BY date DESC
                    """,
                    (username,),
                )
            daily_activity = cur.fetchall()
            
            # Language breakdown: approximate via lexemes table
            try:
                cur.execute(
                    """
                    SELECT l.language, COUNT(*) as reviews
                    FROM lexeme_review_log r
                    JOIN lexemes l ON r.lexeme_id = l.id
                    WHERE r.user_id = %s
                    GROUP BY l.language
                    """,
                    (username,),
                )
                language_breakdown = cur.fetchall()
            except Exception:
                language_breakdown = []
            
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

@app.get("/v1/user/{username}")
def get_user_profile(username: str):
    """Get user profile including CEFR level"""
    conn = db()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user profile
            cur.execute("""
                SELECT username, cefr_level, theta_estimate, last_placement_date, created_at
                FROM simple_users 
                WHERE username = %s
            """, (username,))
            
            user = cur.fetchone()
            
            if user:
                return {
                    "username": user['username'],
                    "cefr_level": user['cefr_level'],
                    "theta_estimate": user['theta_estimate'],
                    "last_placement_date": user['last_placement_date'].isoformat() if user['last_placement_date'] else None,
                    "has_placement": user['last_placement_date'] is not None
                }
            else:
                # Create new user with default level
                cur.execute("""
                    INSERT INTO simple_users (username, cefr_level, theta_estimate)
                    VALUES (%s, 'B1', 0.0)
                    RETURNING username, cefr_level, theta_estimate, last_placement_date, created_at
                """, (username,))
                
                new_user = cur.fetchone()
                return {
                    "username": new_user['username'],
                    "cefr_level": new_user['cefr_level'],
                    "theta_estimate": new_user['theta_estimate'],
                    "last_placement_date": None,
                    "has_placement": False
                }
                
    except Exception as e:
        print(f"User profile error: {e}")
        # Return default profile on error
        return {
            "username": username,
            "cefr_level": "B1",
            "theta_estimate": 0.0,
            "last_placement_date": None,
            "has_placement": False
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
            
            # Handle rating-based placement (1-4 scale)
            # user_answer is now a rating string ("1", "2", "3", "4")
            try:
                user_rating = int(request.user_answer)
            except (ValueError, TypeError):
                user_rating = 2  # Default to "Hard" if invalid
            
            # Convert rating to correctness and confidence for adaptive algorithm
            # More nuanced interpretation for better placement accuracy
            if user_rating == 1:  # Again - definitely wrong
                is_correct = False
                confidence = 1.0  # Very confident it's wrong
            elif user_rating == 2:  # Hard - mostly wrong, some partial knowledge
                is_correct = False  
                confidence = 0.7  # Pretty confident it's wrong, but not completely
            elif user_rating == 3:  # Good - correct
                is_correct = True
                confidence = 0.8  # Confident it's correct
            else:  # Easy - definitely correct
                is_correct = True
                confidence = 1.0  # Very confident it's correct
            
            # Get the actual correct answer for logging purposes
            card_type = card_row.get('type', 'unknown')
            if card_type == 'cloze':
                correct_answer = card_payload.get('answer', '')
            elif card_type == 'vocabulary':
                correct_answer = card_payload.get('translation', '')
            elif card_type == 'sentence':
                correct_answer = card_payload.get('english', '')
            else:
                correct_answer = "Rating-based assessment"
            
            item_theta = card_payload.get('theta', 0.0)
            new_theta, new_se = cat_system.update_ability(
                session['current_theta'], 
                session['theta_se'], 
                item_theta, 
                is_correct,
                confidence
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
                
                # Store user's CEFR level for study system
                cur.execute("""
                    INSERT INTO simple_users (username, cefr_level, theta_estimate, last_placement_date)
                    VALUES (%s, %s, %s, now())
                    ON CONFLICT (username) 
                    DO UPDATE SET 
                        cefr_level = EXCLUDED.cefr_level,
                        theta_estimate = EXCLUDED.theta_estimate,
                        last_placement_date = EXCLUDED.last_placement_date
                """, (session['user_id'], final_cefr, new_theta))
                
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
                    SELECT card_id FROM placement_responses WHERE session_id = %s
                """, (request.session_id,))
                used_items = [row['card_id'] for row in cur.fetchall()]
                
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

# ==================== LLM CONTENT GENERATION ENDPOINTS ====================

@app.post("/v1/generate/content", response_model=GeneratedContentResponse)
async def generate_content_endpoint(request: GenerateContentRequest):
    """Generate a single piece of learning content using LLM"""
    conn = db()
    try:
        result = await generate_single_content(request, conn)
        return result
    except Exception as e:
        print(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/v1/generate/batch", response_model=BatchGenerateResponse)
async def generate_batch_content_endpoint(request: BatchGenerateRequest):
    """Generate multiple pieces of learning content in parallel"""
    conn = db()
    try:
        result = await generate_batch_content(request, conn)
        return result
    except Exception as e:
        print(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/v1/generate/suggestions/{user_cefr}")
async def get_generation_suggestions_endpoint(user_cefr: str, user_id: str = "anonymous", limit: int = 10):
    """Get suggested words for content generation based on user's learning progress"""
    conn = db()
    try:
        suggestions = await get_generation_suggestions(user_cefr, user_id, conn, limit)
        return {
            "user_cefr": user_cefr,
            "user_id": user_id,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        print(f"Generation suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/v1/generate/stats/{user_id}")
async def get_generation_stats(user_id: str):
    """Get content generation statistics for a user"""
    conn = db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get generation counts by type
            cur.execute("""
                SELECT content_type, COUNT(*) as count, 
                       AVG(generation_time_ms) as avg_time_ms,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
                FROM content_generation_log 
                WHERE user_id = %s 
                GROUP BY content_type
                ORDER BY count DESC
            """, (user_id,))
            
            by_type = cur.fetchall()
            
            # Get recent generation history
            cur.execute("""
                SELECT target_word, content_type, success, created_at, generation_time_ms
                FROM content_generation_log 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 20
            """, (user_id,))
            
            recent_history = cur.fetchall()
            
            # Get overall stats
            cur.execute("""
                SELECT COUNT(*) as total_generated,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as total_success,
                       AVG(generation_time_ms) as avg_time_ms,
                       MIN(created_at) as first_generation,
                       MAX(created_at) as last_generation
                FROM content_generation_log 
                WHERE user_id = %s
            """, (user_id,))
            
            overall_stats = cur.fetchone()
            
            return {
                "user_id": user_id,
                "overall_stats": dict(overall_stats) if overall_stats else {},
                "by_content_type": [dict(row) for row in by_type],
                "recent_history": [dict(row) for row in recent_history]
            }
            
    except Exception as e:
        print(f"Generation stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
