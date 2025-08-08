import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

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
        # Insert sample cards
        cur.execute("""
            INSERT INTO cards(language, type, payload)
            VALUES
            ('es','cloze','{"text":"El ___ duerme en la silla.","answer":"gato","hints":["animal doméstico"]}'),
            ('es','cloze','{"text":"Mi ___ bebe leche.","answer":"gato","hints":["animal doméstico"]}'),
            ('es','vocabulary','{"word":"casa","translation":"house","difficulty":"A1"}'),
            ('es','vocabulary','{"word":"agua","translation":"water","difficulty":"A1"}'),
            ('es','sentence','{"spanish":"Hola, ¿cómo estás?","english":"Hello, how are you?","difficulty":"A1"}')
            ON CONFLICT DO NOTHING
        """)
        
        print("Sample cards inserted successfully!")
    
    conn.close()

if __name__ == "__main__":
    run()
