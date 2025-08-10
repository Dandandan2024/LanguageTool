import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

DDL = '''
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  ui_language TEXT DEFAULT 'en',
  target_language TEXT DEFAULT 'es',
  cefr_level TEXT,
  ability_estimate REAL,
  known_word_probs JSONB DEFAULT '{}'::jsonb,
  settings JSONB DEFAULT '{}'::jsonb
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS cards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  language TEXT NOT NULL,
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_cards (
  user_id UUID NOT NULL,
  card_id UUID NOT NULL,
  stability REAL DEFAULT 0,
  difficulty REAL DEFAULT 0.3,
  interval_days REAL DEFAULT 0,
  due_date DATE,
  reps INT DEFAULT 0,
  lapses INT DEFAULT 0,
  last_review TIMESTAMPTZ,
  state TEXT DEFAULT 'new',
  PRIMARY KEY (user_id, card_id)
);

CREATE TABLE IF NOT EXISTS review_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  card_id UUID NOT NULL,
  ts TIMESTAMPTZ DEFAULT now(),
  rating INT CHECK (rating BETWEEN 1 AND 4),
  response_time_ms INT
);
'''
def run():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(DDL)
    print("Database initialized.")
    conn.close()

if __name__ == "__main__":
    run()
