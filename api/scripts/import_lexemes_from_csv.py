import logging
import sys

# Configure logging to file and console
log_file_path = "import_lexemes.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)
    ]
)
import os
import csv
import json
import argparse
from typing import Optional, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from repo root
THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, ".env"))

# Heuristic CEFR mapping by frequency rank (tunable)
DEFAULT_THRESHOLDS = {
    "A1": 1000,
    "A2": 3000,
    "B1": 7000,
    "B2": 15000,
    "C1": 30000,
    "C2": 9999999,
}


def map_cefr_by_rank(rank: Optional[int], thresholds: Dict[str, int]) -> str:
    if rank is None:
        return "B1"
    for level, max_rank in thresholds.items():
        if rank <= max_rank:
            return level
    return "C2"


def db_connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def ensure_schema(cur):
    # Create lexemes table if missing (matches our hybrid schema subset)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lexemes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            language TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT,
            cefr_level TEXT,
            frequency_rank INT,
            payload JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE (language, lemma)
        );
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lexemes_language_lemma ON lexemes(language, lemma);")


def upsert_lexeme(cur, language: str, lemma: str, pos: Optional[str], cefr_level: str, frequency_rank: Optional[int], payload: Optional[dict]):
    payload_json = json.dumps(payload or {}, ensure_ascii=False)
    cur.execute(
        """
        INSERT INTO lexemes (language, lemma, pos, cefr_level, frequency_rank, payload)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (language, lemma)
        DO UPDATE SET
            pos = EXCLUDED.pos,
            cefr_level = EXCLUDED.cefr_level,
            frequency_rank = EXCLUDED.frequency_rank,
            payload = COALESCE(lexemes.payload, '{}'::jsonb) || EXCLUDED.payload
        RETURNING id;
        """,
        (language, lemma, pos, cefr_level, frequency_rank, payload_json),
    )
    row = cur.fetchone()
    return row["id"] if isinstance(row, dict) else row[0]


def get_value(row: dict, *candidates: str) -> Optional[str]:
    # Case-insensitive, trim spaces, accept headers with spaces
    lowered = { (k or '').strip().lower(): v for k, v in row.items() }
    for cand in candidates:
        key = cand.strip().lower()
        if key in lowered:
            return lowered[key]
    return None


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).replace(',', '').strip())
    except Exception:
        return None


def import_lexemes(csv_path: str, language: str = "ru", batch_size: int = 1000, dry_run: bool = False,
                   thresholds: Dict[str, int] = None):
    thresholds = thresholds or DEFAULT_THRESHOLDS

    total_rows = 0
    inserted = 0

    conn = db_connect()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                ensure_schema(cur)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for row in rows:
                    total_rows += 1

                    lemma = (get_value(row, "lemma", "word", "lemma ", "Lemma") or "").strip().lower()
                    if not lemma:
                        continue

                    pos = get_value(row, "pos", "part_of_speech", "POS")
                    pos = (pos or '').strip().lower() or None

                    # frequency_rank from various headers; if missing, None
                    freq_raw = get_value(row, "frequency_rank", "rank", "frequency", "freq", "frq abs", "freq abs")
                    frequency_rank = parse_int(freq_raw)

                    cefr_raw = get_value(row, "cefr_level", "cefr")
                    cefr_level = (cefr_raw or map_cefr_by_rank(frequency_rank, thresholds)).strip().upper()
                    if cefr_level not in {"A1", "A2", "B1", "B2", "C1", "C2"}:
                        cefr_level = map_cefr_by_rank(frequency_rank, thresholds)

                    payload = {}
                    for key in ["notes", "source", "example", "gloss", "morph"]:
                        val = get_value(row, key)
                        if val:
                            payload[key] = val

                    if dry_run:
                        continue

                    _ = upsert_lexeme(cur, language, lemma, pos, cefr_level, frequency_rank, payload)
                    inserted += 1

                    if inserted % batch_size == 0:
                        conn.commit()
                        logging.info(f"Committed {inserted} rows...")

        if not dry_run:
            conn.commit()
        logging.info(f"\n✅ Import complete. Processed: {total_rows}, Upserted: {inserted}")

    except Exception as e:
        logging.error(f"Import failed: {e}", exc_info=True)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import lexemes from CSV into Postgres")
    parser.add_argument("csv_path", help="Path to CSV with columns: lemma,pos,frequency_rank,cefr_level(optional)")
    parser.add_argument("--language", default="ru", help="Language code (default: ru)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Commit batch size (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Parse but do not write to DB")
    args = parser.parse_args()

    import_lexemes(args.csv_path, language=args.language, batch_size=args.batch_size, dry_run=args.dry_run)
