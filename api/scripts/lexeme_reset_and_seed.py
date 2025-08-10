import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Allow running from repo root or api/
SCRIPT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
API_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Load .env at repo root
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, ".env"))

# Map CEFR -> theta
CEFR_THETA = {"A1": -2.0, "A2": -1.0, "B1": 0.0, "B2": 1.0, "C1": 2.0, "C2": 3.0}

# How many lexemes to seed
DEFAULT_LEXEME_LIMIT = int(os.getenv("LEXEME_SEED_LIMIT", "20"))


def db_connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def backup_and_reset(cur):
    now_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    # Ensure cards has lexeme_id
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'lexeme_id'
            ) THEN
                ALTER TABLE cards ADD COLUMN lexeme_id UUID NULL;
            END IF;
        END$$;
    """)

    # Backups
    print("Creating backups of cards, user_cards, review_log ...")
    cur.execute(f"CREATE TABLE IF NOT EXISTS cards_backup_{now_suffix} AS SELECT * FROM cards;")
    cur.execute(f"CREATE TABLE IF NOT EXISTS user_cards_backup_{now_suffix} AS SELECT * FROM user_cards;")
    cur.execute(f"CREATE TABLE IF NOT EXISTS review_log_backup_{now_suffix} AS SELECT * FROM review_log;")

    # Reset
    print("Truncating cards, user_cards, review_log ...")
    cur.execute("TRUNCATE TABLE review_log;")
    cur.execute("TRUNCATE TABLE user_cards;")
    cur.execute("TRUNCATE TABLE cards;")

    # Index for lexeme_id
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_lexeme_id ON cards(lexeme_id);")


def pick_seed_lexemes(cur, limit: int):
    # Prefer lexemes with frequency and CEFR; else fallback to any RU lexemes
    cur.execute(
        """
        SELECT id, lemma, pos, cefr_level, frequency_rank
        FROM lexemes
        WHERE language = 'ru'
        ORDER BY COALESCE(frequency_rank, 999999) ASC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    print(f"Selected {len(rows)} lexemes to seed")
    return rows


def build_payload(question: str, answer: str, target_word: str, theta: float, supporting_words: list, cefr_level: str, generation_method: str):
    return json.dumps({
        "question": question,
        "answer": answer,
        "target_word": target_word,
        "theta": theta,
        "supporting_words": supporting_words,
        "generation_metadata": {
            "cefr_level": cefr_level,
            "generation_method": generation_method
        }
    }, ensure_ascii=False)


def seed_cards_for_lexemes(conn, cur, lexemes):
    # Use the existing content generator to ensure consistent prompts/format
    sys.path.append(API_DIR)
    from llm.content_generator import ContentGenerator, GenerationRequest, ContentType, CEFRLevel

    generator = ContentGenerator(conn)
    inserted = 0

    for lx in lexemes:
        lexeme_id = lx[0]
        lemma = lx[1]
        cefr = lx[3] or 'B1'
        theta = CEFR_THETA.get(cefr, 0.0)

        # Prepare generation requests (one vocabulary + one sentence)
        gen_reqs = [
            GenerationRequest(
                target_word=lemma,
                target_lexeme_id=str(lexeme_id),
                content_type=ContentType.VOCABULARY,
                user_cefr=CEFRLevel(cefr if cefr in CEFRLevel.__members__ else 'B1'),
                user_id="seed"
            ),
            GenerationRequest(
                target_word=lemma,
                target_lexeme_id=str(lexeme_id),
                content_type=ContentType.SENTENCE,
                user_cefr=CEFRLevel(cefr if cefr in CEFRLevel.__members__ else 'B1'),
                user_id="seed"
            )
        ]

        for req in gen_reqs:
            try:
                # Generate synchronously by calling internal methods through public API
                content = None
                # Use underlying private to avoid asyncio in this script
                if req.content_type.value == 'vocabulary':
                    content = generator._generate_vocabulary_card(req, {  # type: ignore
                        'target_theta': theta,
                        'complexity_guidelines': 'auto',
                        'max_sentence_length': 15
                    })
                elif req.content_type.value == 'sentence':
                    content = generator._generate_sentence_card(req, {  # type: ignore
                        'target_theta': theta,
                        'complexity_guidelines': 'auto',
                        'max_sentence_length': 15
                    })
                else:
                    continue

                # Await if coroutine
                if hasattr(content, "__await__"):
                    import asyncio
                    content = asyncio.get_event_loop().run_until_complete(content)  # type: ignore

                payload = build_payload(
                    content.question_text,
                    content.answer_text,
                    content.target_word,
                    theta,
                    content.supporting_words,
                    cefr,
                    content.metadata.get("generation_method", "llm")
                )

                cur.execute(
                    """
                    INSERT INTO cards (type, language, payload, lexeme_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (req.content_type.value, 'ru', payload, lexeme_id)
                )
                new_id = cur.fetchone()[0]

                # Log generation
                cur.execute(
                    """
                    INSERT INTO content_generation_log (
                        user_id, card_id, target_word, content_type, cefr_level, generation_method
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (req.user_id, str(new_id), req.target_word, req.content_type.value, cefr, content.metadata.get("generation_method", "llm"))
                )

                inserted += 1

            except Exception as e:
                print(f"Failed to generate for lexeme {lemma}: {e}")
                conn.rollback()
                continue

    print(f"Inserted {inserted} new GPT-5-backed cards")


def main():
    limit = DEFAULT_LEXEME_LIMIT
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except Exception:
            pass

    conn = db_connect()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                backup_and_reset(cur)
                lexemes = pick_seed_lexemes(cur, limit)

        # Use a separate cursor without context manager to reuse connection in generator
        with conn:
            with conn.cursor() as cur2:
                seed_cards_for_lexemes(conn, cur2, lexemes)

        conn.commit()
        print("\n✅ Lexeme-first reset complete. New cards seeded.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


