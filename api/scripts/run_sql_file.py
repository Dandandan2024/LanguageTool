import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def run_sql_file(filename):
    """Run a SQL file against the database"""
    
    # Read the SQL file
    script_dir = os.path.dirname(__file__)
    sql_file_path = os.path.join(script_dir, filename)
    
    if not os.path.exists(sql_file_path):
        print(f"SQL file not found: {sql_file_path}")
        return
    
    with open(sql_file_path, 'r', encoding='utf-8') as file:
        sql_content = file.read()
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Execute the SQL content
            cur.execute(sql_content)
            print(f"Successfully executed {filename}")
            print("Russian content added to database!")
    except Exception as e:
        print(f"Error executing SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Run placement cards setup
    run_sql_file("create_placement_cards.sql")
