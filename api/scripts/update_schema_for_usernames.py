#!/usr/bin/env python3
"""
Update database schema to support username-based progress tracking
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def update_schema():
    """Update database schema for username support"""
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        sslmode=os.getenv("POSTGRES_SSLMODE", "prefer")
    )
    
    try:
        with conn, conn.cursor() as cur:
            print("Updating database schema for username support...")
            
            # Check if review_log table exists and what columns it has
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'review_log'
            """)
            columns = cur.fetchall()
            print(f"Current review_log columns: {columns}")
            
            # Update user_id column to TEXT if it's UUID
            try:
                cur.execute("""
                    ALTER TABLE review_log 
                    ALTER COLUMN user_id TYPE TEXT
                """)
                print("✅ Updated user_id column to TEXT")
            except Exception as e:
                print(f"⚠️ Could not alter user_id column: {e}")
                # Try creating a new table if alteration fails
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS review_log_new (
                        id BIGSERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        card_id TEXT NOT NULL,
                        ts TIMESTAMPTZ DEFAULT now(),
                        rating INT CHECK (rating BETWEEN 1 AND 4),
                        response_time_ms INT
                    )
                """)
                
                # Copy existing data if any
                cur.execute("""
                    INSERT INTO review_log_new (user_id, card_id, ts, rating, response_time_ms)
                    SELECT user_id::TEXT, card_id::TEXT, ts, rating, response_time_ms 
                    FROM review_log
                    ON CONFLICT DO NOTHING
                """)
                
                # Rename tables
                cur.execute("DROP TABLE IF EXISTS review_log_old")
                cur.execute("ALTER TABLE review_log RENAME TO review_log_old")
                cur.execute("ALTER TABLE review_log_new RENAME TO review_log")
                print("✅ Created new review_log table with TEXT columns")
            
            # Also update user_cards table if it exists
            try:
                cur.execute("""
                    ALTER TABLE user_cards 
                    ALTER COLUMN user_id TYPE TEXT,
                    ALTER COLUMN card_id TYPE TEXT
                """)
                print("✅ Updated user_cards columns to TEXT")
            except Exception as e:
                print(f"⚠️ Could not alter user_cards: {e}")
            
            # Verify the changes
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'review_log'
            """)
            new_columns = cur.fetchall()
            print(f"Updated review_log columns: {new_columns}")
            
            print("✅ Database schema update completed!")
            
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_schema()
