"""
Add CEFR level tracking to simple_users table
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def update_users_table():
    """Add CEFR level columns to simple_users table"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    try:
        with conn, conn.cursor() as cur:
            # Ensure simple_users table exists with CEFR fields
            cur.execute("""
                CREATE TABLE IF NOT EXISTS simple_users (
                    username TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    cefr_level TEXT DEFAULT 'B1',
                    theta_estimate REAL DEFAULT 0.0,
                    last_placement_date TIMESTAMPTZ
                );
            """)
            
            # Add columns if they don't exist (for existing tables)
            try:
                cur.execute("ALTER TABLE simple_users ADD COLUMN IF NOT EXISTS cefr_level TEXT DEFAULT 'B1';")
                cur.execute("ALTER TABLE simple_users ADD COLUMN IF NOT EXISTS theta_estimate REAL DEFAULT 0.0;")
                cur.execute("ALTER TABLE simple_users ADD COLUMN IF NOT EXISTS last_placement_date TIMESTAMPTZ;")
                print("✅ Added CEFR columns to simple_users table")
            except Exception as e:
                print(f"Note: Columns may already exist: {e}")
            
            conn.commit()
            print("✅ Users table updated successfully!")
            
    except Exception as e:
        print(f"❌ Error updating users table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_users_table()
