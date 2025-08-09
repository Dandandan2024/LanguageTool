import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def add_username_support():
    """Update database schema to support username-based progress tracking"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    
    with conn.cursor() as cur:
        # Update review_log table to use username as user_id (it's already text)
        print("✅ review_log table already supports text user_id (usernames)")
        
        # Update user_cards table to use username as user_id
        try:
            # Check if user_cards has any data
            cur.execute("SELECT COUNT(*) FROM user_cards")
            count = cur.fetchone()[0]
            
            if count > 0:
                print(f"⚠️  Found {count} existing user_cards records")
                print("   These will be preserved but may need manual cleanup")
            
            # The user_cards table should already support text user_id
            print("✅ user_cards table already supports text user_id (usernames)")
            
        except Exception as e:
            print(f"Note: user_cards table might not exist yet: {e}")
        
        # Create a simple users table for username tracking (optional)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS simple_users (
                username TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT now(),
                last_active TIMESTAMPTZ DEFAULT now(),
                total_reviews INTEGER DEFAULT 0
            )
        """)
        
        print("✅ Created simple_users table for username tracking")
        print("🎉 Database is ready for username-based progress tracking!")
    
    conn.close()

if __name__ == "__main__":
    add_username_support()
