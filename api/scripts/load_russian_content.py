import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def load_russian_sql():
    """Load Russian content from SQL file into database"""
    
    # Read the SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), "russian_content.sql")
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    
    # Execute the SQL
    with conn.cursor() as cur:
        cur.execute(sql_content)
        print("✅ Russian content loaded successfully!")
    
    conn.close()

if __name__ == "__main__":
    load_russian_sql()
