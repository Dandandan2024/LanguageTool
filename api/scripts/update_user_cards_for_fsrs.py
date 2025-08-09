"""
Update user_cards table to support full FSRS v4 implementation
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def update_user_cards_table():
    """Update user_cards table with proper FSRS fields"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    try:
        with conn, conn.cursor() as cur:
            print("Updating user_cards table for FSRS v4...")
            
            # Add missing columns if they don't exist
            try:
                cur.execute("ALTER TABLE user_cards ADD COLUMN IF NOT EXISTS scheduled_days INT DEFAULT 0;")
                cur.execute("ALTER TABLE user_cards ADD COLUMN IF NOT EXISTS elapsed_days INT DEFAULT 0;")
                print("✅ Added scheduled_days and elapsed_days columns")
            except Exception as e:
                print(f"Note: Columns may already exist: {e}")
            
            # Update existing columns to have better defaults
            cur.execute("""
                ALTER TABLE user_cards 
                ALTER COLUMN stability SET DEFAULT 0.0,
                ALTER COLUMN difficulty SET DEFAULT 0.0,
                ALTER COLUMN interval_days SET DEFAULT 0.0,
                ALTER COLUMN reps SET DEFAULT 0,
                ALTER COLUMN lapses SET DEFAULT 0;
            """)
            
            # Update state column to use FSRS states
            cur.execute("ALTER TABLE user_cards ALTER COLUMN state SET DEFAULT 'new';")
            
            print("✅ Updated column defaults")
            
            # Add index for due_date queries (performance optimization)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_cards_due_date 
                ON user_cards(user_id, due_date) 
                WHERE due_date IS NOT NULL;
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_cards_state 
                ON user_cards(user_id, state);
            """)
            
            print("✅ Added performance indexes")
            
            # Show current table structure
            cur.execute("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_cards'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            print("\n📊 Current user_cards table structure:")
            for col in columns:
                print(f"  {col[0]}: {col[1]} (default: {col[2]}, nullable: {col[3]})")
            
            conn.commit()
            print("\n✅ user_cards table updated successfully for FSRS v4!")
            
    except Exception as e:
        print(f"❌ Error updating user_cards table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_user_cards_table()
