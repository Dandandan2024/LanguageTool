#!/usr/bin/env python3
import os
import csv
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from repo root
THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, ".env"))

# CEFR mapping by frequency rank
DEFAULT_THRESHOLDS = {
    "A1": 1000,
    "A2": 3000,
    "B1": 7000,
    "B2": 15000,
    "C1": 30000,
    "C2": 9999999,
}

def map_cefr_by_rank(rank, thresholds=DEFAULT_THRESHOLDS):
    if rank is None:
        return "B1"
    for level, max_rank in thresholds.items():
        if rank <= max_rank:
            return level
    return "C2"

def db_connect_with_retry(max_retries=3):
    """Connect to database with retry logic"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
            return conn
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise

def ensure_schema(cur):
    """Create lexemes table if missing"""
    cur.execute("""
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
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lexemes_language_lemma ON lexemes(language, lemma);")

def clear_and_reset_database():
    """Clear all existing data and prepare for fresh lexeme-based system"""
    print("🗑️  Clearing existing data and preparing fresh lexeme-based system...")
    
    conn = db_connect_with_retry()
    try:
        with conn:
            with conn.cursor() as cur:
                # Backup existing data with timestamp
                from datetime import datetime
                backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                print("📦 Creating backups...")
                cur.execute(f"CREATE TABLE IF NOT EXISTS cards_backup_{backup_suffix} AS SELECT * FROM cards;")
                cur.execute(f"CREATE TABLE IF NOT EXISTS user_cards_backup_{backup_suffix} AS SELECT * FROM user_cards;")
                cur.execute(f"CREATE TABLE IF NOT EXISTS review_log_backup_{backup_suffix} AS SELECT * FROM review_log;")
                
                # Clear all existing data
                print("🧹 Clearing tables...")
                cur.execute("TRUNCATE TABLE review_log CASCADE;")
                cur.execute("TRUNCATE TABLE user_cards CASCADE;")
                cur.execute("TRUNCATE TABLE cards CASCADE;")
                cur.execute("TRUNCATE TABLE lexemes CASCADE;")
                
                # Add lexeme_id column to cards if it doesn't exist
                print("🔧 Adding lexeme_id column to cards...")
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'cards' AND column_name = 'lexeme_id'
                        ) THEN
                            ALTER TABLE cards ADD COLUMN lexeme_id UUID NULL;
                        END IF;
                    END$$;
                """)
                
                # Create index for lexeme_id
                cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_lexeme_id ON cards(lexeme_id);")
                
                # Ensure lexemes schema
                ensure_schema(cur)
                
        conn.commit()
        print("✅ Database cleared and prepared for lexeme-based system")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def import_lexemes_robust(csv_path, batch_size=500):
    """Import lexemes with robust error handling"""
    print(f"📥 Starting robust lexeme import from {csv_path}")
    
    # Read all CSV data first
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"📊 Found {len(rows)} rows to import")
    
    total_imported = 0
    batch_start = 0
    
    while batch_start < len(rows):
        batch_end = min(batch_start + batch_size, len(rows))
        batch_rows = rows[batch_start:batch_end]
        
        try:
            conn = db_connect_with_retry()
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    ensure_schema(cur)
                    
                    for row in batch_rows:
                        lemma = (row.get("lemma", "") or "").strip().lower()
                        if not lemma:
                            continue
                        
                        pos = (row.get("pos", "") or "").strip().lower() or None
                        
                        # Parse frequency rank
                        freq_raw = row.get("frequency_rank", "")
                        try:
                            frequency_rank = int(freq_raw) if freq_raw else None
                        except:
                            frequency_rank = None
                        
                        # Determine CEFR level
                        cefr_raw = row.get("cefr_level", "")
                        if cefr_raw and cefr_raw.upper() in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                            cefr_level = cefr_raw.upper()
                        else:
                            cefr_level = map_cefr_by_rank(frequency_rank)
                        
                        # Upsert lexeme
                        cur.execute("""
                            INSERT INTO lexemes (language, lemma, pos, cefr_level, frequency_rank, payload)
                            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                            ON CONFLICT (language, lemma)
                            DO UPDATE SET
                                pos = EXCLUDED.pos,
                                cefr_level = EXCLUDED.cefr_level,
                                frequency_rank = EXCLUDED.frequency_rank,
                                payload = COALESCE(lexemes.payload, '{}'::jsonb) || EXCLUDED.payload
                        """, ("ru", lemma, pos, cefr_level, frequency_rank, "{}"))
                        
                        total_imported += 1
                
                conn.commit()
                print(f"✅ Imported batch {batch_start + 1}-{batch_end} ({total_imported} total)")
                
        except Exception as e:
            print(f"❌ Error in batch {batch_start + 1}-{batch_end}: {e}")
            print("⏳ Waiting 5 seconds before retrying...")
            time.sleep(5)
            continue
        finally:
            if 'conn' in locals():
                conn.close()
        
        batch_start = batch_end
    
    print(f"🎉 Import complete! Total imported: {total_imported}")
    return total_imported

def verify_import():
    """Verify the import was successful"""
    print("🔍 Verifying import...")
    
    conn = db_connect_with_retry()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Count total lexemes
            cur.execute("SELECT COUNT(*) as count FROM lexemes WHERE language = 'ru'")
            total_count = cur.fetchone()['count']
            print(f"📊 Total Russian lexemes: {total_count}")
            
            # CEFR breakdown
            cur.execute("""
                SELECT cefr_level, COUNT(*) as count 
                FROM lexemes WHERE language = 'ru' 
                GROUP BY cefr_level ORDER BY cefr_level
            """)
            breakdown = cur.fetchall()
            print("📈 CEFR breakdown:")
            for row in breakdown:
                print(f"  {row['cefr_level']}: {row['count']} lexemes")
            
            # Sample lexemes
            cur.execute("""
                SELECT lemma, pos, cefr_level, frequency_rank 
                FROM lexemes WHERE language = 'ru' 
                ORDER BY frequency_rank NULLS LAST 
                LIMIT 10
            """)
            samples = cur.fetchall()
            print("\n🔤 Sample lexemes (by frequency):")
            for row in samples:
                rank = row['frequency_rank'] or 'N/A'
                print(f"  {row['lemma']} ({row['pos']}) - {row['cefr_level']} - rank {rank}")
                
    except Exception as e:
        print(f"❌ Error verifying import: {e}")
    finally:
        conn.close()

def main():
    csv_path = os.path.join(REPO_ROOT, "lexemes_ru_normalized.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    try:
        # Step 1: Clear and reset database
        clear_and_reset_database()
        
        # Step 2: Import lexemes
        import_lexemes_robust(csv_path, batch_size=500)
        
        # Step 3: Verify import
        verify_import()
        
        print("\n🎉 Lexeme-based system setup complete!")
        print("Next steps:")
        print("1. Generate cards using LLM flow")
        print("2. Test the API with new lexeme-based cards")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
